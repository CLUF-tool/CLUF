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

package org.apache.kylin.engine.mr.steps;

import java.io.IOException;
import java.util.Map;
import java.util.Map.Entry;

import org.apache.commons.cli.Options;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.mapreduce.lib.output.SequenceFileOutputFormat;
import org.apache.hadoop.util.ToolRunner;
import org.apache.kylin.common.KylinConfig;
import org.apache.kylin.cube.CubeInstance;
import org.apache.kylin.cube.CubeManager;
import org.apache.kylin.cube.CubeSegment;
import org.apache.kylin.engine.mr.ByteArrayWritable;
import org.apache.kylin.engine.mr.CubingJob;
import org.apache.kylin.engine.mr.HadoopUtil;
import org.apache.kylin.engine.mr.IMRInput.IMRTableInputFormat;
import org.apache.kylin.engine.mr.MRUtil;
import org.apache.kylin.engine.mr.common.AbstractHadoopJob;
import org.apache.kylin.engine.mr.common.BatchConstants;
import org.apache.kylin.engine.mr.common.CubeStatsReader;
import org.apache.kylin.job.manager.ExecutableManager;
import org.apache.kylin.metadata.model.SegmentStatusEnum;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 */
public class InMemCuboidJob extends AbstractHadoopJob {

    protected static final Logger logger = LoggerFactory.getLogger(InMemCuboidJob.class);

    private boolean skipped = false;

    @Override
    public boolean isSkipped() {
        return skipped;
    }

    private boolean checkSkip(String cubingJobId) {
        if (cubingJobId == null)
            return false;

        ExecutableManager execMgr = ExecutableManager.getInstance(KylinConfig.getInstanceFromEnv());
        CubingJob cubingJob = (CubingJob) execMgr.getJob(cubingJobId);
        skipped = cubingJob.isInMemCubing() == false;
        return skipped;
    }

    @Override
    public int run(String[] args) throws Exception {
        Options options = new Options();

        try {
            options.addOption(OPTION_JOB_NAME);
            options.addOption(OPTION_CUBE_NAME);
            options.addOption(OPTION_SEGMENT_NAME);
            options.addOption(OPTION_OUTPUT_PATH);
            options.addOption(OPTION_CUBING_JOB_ID);
            parseOptions(options, args);

            String cubeName = getOptionValue(OPTION_CUBE_NAME).toUpperCase();
            String segmentName = getOptionValue(OPTION_SEGMENT_NAME);
            String output = getOptionValue(OPTION_OUTPUT_PATH);

            KylinConfig config = KylinConfig.getInstanceFromEnv();
            CubeManager cubeMgr = CubeManager.getInstance(config);
            CubeInstance cube = cubeMgr.getCube(cubeName);
            config = cube.getConfig();
            CubeSegment cubeSeg = cube.getSegment(segmentName, SegmentStatusEnum.NEW);
            String cubingJobId = getOptionValue(OPTION_CUBING_JOB_ID);

            if (checkSkip(cubingJobId)) {
                logger.info("Skip job " + getOptionValue(OPTION_JOB_NAME) + " for " + cubeSeg);
                return 0;
            }

            job = Job.getInstance(getConf(), getOptionValue(OPTION_JOB_NAME));
            logger.info("Starting: " + job.getJobName());
            
            // some special tuning for in-mem MR job
            overrideJobConf(job.getConfiguration(), config);

            setJobClasspath(job);

            // add metadata to distributed cache
            attachKylinPropsAndMetadata(cube, job.getConfiguration());

            // set job configuration
            job.getConfiguration().set(BatchConstants.CFG_CUBE_NAME, cubeName);
            job.getConfiguration().set(BatchConstants.CFG_CUBE_SEGMENT_NAME, segmentName);
            long timeout = 1000 * 60 * 60L; // 1 hour
            job.getConfiguration().set("mapred.task.timeout", String.valueOf(timeout));

            // set input
            IMRTableInputFormat flatTableInputFormat = MRUtil.getBatchCubingInputSide(cubeSeg).getFlatTableInputFormat();
            flatTableInputFormat.configureJob(job);

            // set mapper
            job.setMapperClass(InMemCuboidMapper.class);
            job.setMapOutputKeyClass(ByteArrayWritable.class);
            job.setMapOutputValueClass(ByteArrayWritable.class);

            // set output
            job.setReducerClass(InMemCuboidReducer.class);
            job.setNumReduceTasks(calculateReducerNum(cubeSeg));

            // the cuboid file and KV class must be compatible with 0.7 version for smooth upgrade
            job.setOutputFormatClass(SequenceFileOutputFormat.class);
            job.setOutputKeyClass(Text.class);
            job.setOutputValueClass(Text.class);

            Path outputPath = new Path(output);
            FileOutputFormat.setOutputPath(job, outputPath);

            HadoopUtil.deletePath(job.getConfiguration(), outputPath);

            return waitForCompletion(job);
        } catch (Exception e) {
            logger.error("error in CuboidJob", e);
            printUsage(options);
            throw e;
        } finally {
            if (job != null)
                cleanupTempConfFile(job.getConfiguration());
        }
    }

    private void overrideJobConf(Configuration jobConf, KylinConfig kylinConfig) {
        for (Entry<String, String> entry : kylinConfig.getCubingInMemMRJobConfOverride().entrySet()) {
            jobConf.set(entry.getKey(), entry.getValue());
        }
    }

    private int calculateReducerNum(CubeSegment cubeSeg) throws IOException {
        KylinConfig kylinConfig = cubeSeg.getConfig();

        Map<Long, Double> cubeSizeMap = new CubeStatsReader(cubeSeg, kylinConfig).getCuboidSizeMap();
        double totalSizeInM = 0;
        for (Double cuboidSize : cubeSizeMap.values()) {
            totalSizeInM += cuboidSize;
        }

        double perReduceInputMB = kylinConfig.getDefaultHadoopJobReducerInputMB();

        // number of reduce tasks
        int numReduceTasks = (int) Math.round(totalSizeInM / perReduceInputMB);

        // at least 1 reducer
        numReduceTasks = Math.max(1, numReduceTasks);
        // no more than 5000 reducer by default
        numReduceTasks = Math.min(kylinConfig.getHadoopJobMaxReducerNumber(), numReduceTasks);

        logger.info("Having total map input MB " + Math.round(totalSizeInM));
        logger.info("Having per reduce MB " + perReduceInputMB);
        logger.info("Setting " + "mapred.reduce.tasks" + "=" + numReduceTasks);
        return numReduceTasks;
    }

    public static void main(String[] args) throws Exception {
        InMemCuboidJob job = new InMemCuboidJob();
        int exitCode = ToolRunner.run(job, args);
        System.exit(exitCode);
    }
}
