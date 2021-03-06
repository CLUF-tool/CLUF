/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 * 
 *     http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
*/

package org.apache.kylin.storage.hbase.steps;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.apache.commons.cli.Options;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IOUtils;
import org.apache.hadoop.io.SequenceFile;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.Writable;
import org.apache.hadoop.util.ReflectionUtils;
import org.apache.hadoop.util.StringUtils;
import org.apache.hadoop.util.ToolRunner;
import org.apache.kylin.common.KylinConfig;
import org.apache.kylin.common.util.Bytes;
import org.apache.kylin.common.util.BytesUtil;
import org.apache.kylin.common.util.Primes;
import org.apache.kylin.common.util.ShardingHash;
import org.apache.kylin.cube.CubeInstance;
import org.apache.kylin.cube.CubeManager;
import org.apache.kylin.cube.CubeSegment;
import org.apache.kylin.cube.model.CubeDesc;
import org.apache.kylin.engine.mr.common.AbstractHadoopJob;
import org.apache.kylin.engine.mr.common.CubeStatsReader;
import org.apache.kylin.engine.mr.common.CuboidShardUtil;
import org.apache.kylin.engine.mr.steps.InMemCuboidJob;
import org.apache.kylin.metadata.model.DataModelDesc;
import org.apache.kylin.metadata.model.SegmentStatusEnum;
import org.apache.kylin.storage.hbase.HBaseConnection;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.common.collect.Lists;
import com.google.common.collect.Maps;

/**
 */
public class CreateHTableJob extends AbstractHadoopJob {

    protected static final Logger logger = LoggerFactory.getLogger(CreateHTableJob.class);

    CubeInstance cube = null;
    CubeDesc cubeDesc = null;
    String segmentName = null;
    KylinConfig kylinConfig;

    @Override
    public int run(String[] args) throws Exception {
        Options options = new Options();

        options.addOption(OPTION_CUBE_NAME);
        options.addOption(OPTION_SEGMENT_NAME);
        options.addOption(OPTION_PARTITION_FILE_PATH);
        options.addOption(OPTION_STATISTICS_ENABLED);
        parseOptions(options, args);

        Path partitionFilePath = new Path(getOptionValue(OPTION_PARTITION_FILE_PATH));
        boolean statsEnabled = Boolean.parseBoolean(getOptionValue(OPTION_STATISTICS_ENABLED));

        String cubeName = getOptionValue(OPTION_CUBE_NAME).toUpperCase();
        CubeManager cubeMgr = CubeManager.getInstance(KylinConfig.getInstanceFromEnv());
        cube = cubeMgr.getCube(cubeName);
        cubeDesc = cube.getDescriptor();
        kylinConfig = cube.getConfig();
        segmentName = getOptionValue(OPTION_SEGMENT_NAME);
        CubeSegment cubeSegment = cube.getSegment(segmentName, SegmentStatusEnum.NEW);

        Configuration conf = HBaseConnection.getCurrentHBaseConfiguration();

        try {
            byte[][] splitKeys;
            if (statsEnabled) {
                final Map<Long, Double> cuboidSizeMap = new CubeStatsReader(cubeSegment, kylinConfig).getCuboidSizeMap();
                splitKeys = getSplitsFromCuboidStatistics(cuboidSizeMap, kylinConfig, cubeSegment);
            } else {
                splitKeys = getSplits(conf, partitionFilePath);
            }

            CubeHTableUtil.createHTable(cubeSegment, splitKeys);
            return 0;
        } catch (Exception e) {
            printUsage(options);
            e.printStackTrace(System.err);
            logger.error(e.getLocalizedMessage(), e);
            return 2;
        }
    }

    @SuppressWarnings("deprecation")
    public byte[][] getSplits(Configuration conf, Path path) throws Exception {
        FileSystem fs = path.getFileSystem(conf);
        if (fs.exists(path) == false) {
            System.err.println("Path " + path + " not found, no region split, HTable will be one region");
            return null;
        }

        List<byte[]> rowkeyList = new ArrayList<byte[]>();
        SequenceFile.Reader reader = null;
        try {
            reader = new SequenceFile.Reader(fs, path, conf);
            Writable key = (Writable) ReflectionUtils.newInstance(reader.getKeyClass(), conf);
            Writable value = (Writable) ReflectionUtils.newInstance(reader.getValueClass(), conf);
            while (reader.next(key, value)) {
                rowkeyList.add(((Text) key).copyBytes());
            }
        } catch (Exception e) {
            e.printStackTrace();
            throw e;
        } finally {
            IOUtils.closeStream(reader);
        }

        logger.info((rowkeyList.size() + 1) + " regions");
        logger.info(rowkeyList.size() + " splits");
        for (byte[] split : rowkeyList) {
            logger.info(StringUtils.byteToHexString(split));
        }

        byte[][] retValue = rowkeyList.toArray(new byte[rowkeyList.size()][]);
        return retValue.length == 0 ? null : retValue;
    }

    //one region for one shard
    private static byte[][] getSplitsByRegionCount(int regionCount) {
        byte[][] result = new byte[regionCount - 1][];
        for (int i = 1; i < regionCount; ++i) {
            byte[] split = new byte[Bytes.SIZEOF_SHORT];
            BytesUtil.writeUnsigned(i, split, 0, Bytes.SIZEOF_SHORT);
            result[i - 1] = split;
        }
        return result;
    }

    public static byte[][] getSplitsFromCuboidStatistics(final Map<Long, Double> cubeSizeMap, KylinConfig kylinConfig, CubeSegment cubeSegment) throws IOException {

        final CubeDesc cubeDesc = cubeSegment.getCubeDesc();

        DataModelDesc.RealizationCapacity cubeCapacity = cubeDesc.getModel().getCapacity();
        int cut = kylinConfig.getHBaseRegionCut(cubeCapacity.toString());

        logger.info("Cube capacity " + cubeCapacity.toString() + ", chosen cut for HTable is " + cut + "GB");

        double totalSizeInM = 0;
        for (Double cuboidSize : cubeSizeMap.values()) {
            totalSizeInM += cuboidSize;
        }

        List<Long> allCuboids = Lists.newArrayList();
        allCuboids.addAll(cubeSizeMap.keySet());
        Collections.sort(allCuboids);

        int nRegion = Math.round((float) (totalSizeInM / (cut * 1024L)));
        nRegion = Math.max(kylinConfig.getHBaseRegionCountMin(), nRegion);
        nRegion = Math.min(kylinConfig.getHBaseRegionCountMax(), nRegion);

        if (cubeSegment.isEnableSharding()) {//&& (nRegion > 1)) {
            //use prime nRegions to help random sharding
            int original = nRegion;
            nRegion = Primes.nextPrime(nRegion);//return 2 for input 1

            if (nRegion > Short.MAX_VALUE) {
                logger.info("Too many regions! reduce to " + Short.MAX_VALUE);
                nRegion = Short.MAX_VALUE;
            }

            if (nRegion != original) {
                logger.info("Region count is adjusted from " + original + " to " + nRegion + " to help random sharding");
            }
        }

        int mbPerRegion = (int) (totalSizeInM / nRegion);
        mbPerRegion = Math.max(1, mbPerRegion);

        logger.info("Total size " + totalSizeInM + "M (estimated)");
        logger.info("Expecting " + nRegion + " regions.");
        logger.info("Expecting " + mbPerRegion + " MB per region.");

        if (cubeSegment.isEnableSharding()) {
            //each cuboid will be split into different number of shards
            HashMap<Long, Short> cuboidShards = Maps.newHashMap();
            double[] regionSizes = new double[nRegion];
            for (long cuboidId : allCuboids) {
                double estimatedSize = cubeSizeMap.get(cuboidId);
                double magic = 23;
                int shardNum = (int) (estimatedSize * magic / mbPerRegion + 1);
                if (shardNum < 1) {
                    shardNum = 1;
                }

                if (shardNum > nRegion) {
                    logger.info(String.format("Cuboid %d 's estimated size %.2f MB will generate %d regions, reduce to %d", cuboidId, estimatedSize, shardNum, nRegion));
                    shardNum = nRegion;
                } else {
                    logger.info(String.format("Cuboid %d 's estimated size %.2f MB will generate %d regions", cuboidId, estimatedSize, shardNum));
                }

                cuboidShards.put(cuboidId, (short) shardNum);
                short startShard = ShardingHash.getShard(cuboidId, nRegion);
                for (short i = startShard; i < startShard + shardNum; ++i) {
                    short j = (short) (i % nRegion);
                    regionSizes[j] = regionSizes[j] + estimatedSize / shardNum;
                }
            }

            for (int i = 0; i < nRegion; ++i) {
                logger.info(String.format("Region %d's estimated size is %.2f MB, accounting for %.2f percent", i, regionSizes[i], 100.0 * regionSizes[i] / totalSizeInM));
            }

            CuboidShardUtil.saveCuboidShards(cubeSegment, cuboidShards, nRegion);

            return getSplitsByRegionCount(nRegion);

        } else {
            List<Long> regionSplit = Lists.newArrayList();

            long size = 0;
            int regionIndex = 0;
            int cuboidCount = 0;
            for (int i = 0; i < allCuboids.size(); i++) {
                long cuboidId = allCuboids.get(i);
                if (size >= mbPerRegion || (size + cubeSizeMap.get(cuboidId)) >= mbPerRegion * 1.2) {
                    // if the size already bigger than threshold, or it will exceed by 20%, cut for next region
                    regionSplit.add(cuboidId);
                    logger.info("Region " + regionIndex + " will be " + size + " MB, contains cuboids < " + cuboidId + " (" + cuboidCount + ") cuboids");
                    size = 0;
                    cuboidCount = 0;
                    regionIndex++;
                }
                size += cubeSizeMap.get(cuboidId);
                cuboidCount++;
            }

            byte[][] result = new byte[regionSplit.size()][];
            for (int i = 0; i < regionSplit.size(); i++) {
                result[i] = Bytes.toBytes(regionSplit.get(i));
            }

            return result;
        }
    }

    public static void main(String[] args) throws Exception {
        int exitCode = ToolRunner.run(new CreateHTableJob(), args);
        System.exit(exitCode);
    }
}
