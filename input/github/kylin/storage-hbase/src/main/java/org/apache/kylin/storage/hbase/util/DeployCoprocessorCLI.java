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

package org.apache.kylin.storage.hbase.util;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;

import org.apache.commons.io.IOUtils;
import org.apache.commons.lang.StringUtils;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FSDataOutputStream;
import org.apache.hadoop.fs.FileStatus;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.hbase.HConstants;
import org.apache.hadoop.hbase.HTableDescriptor;
import org.apache.hadoop.hbase.TableName;
import org.apache.hadoop.hbase.TableNotFoundException;
import org.apache.hadoop.hbase.client.HBaseAdmin;
import org.apache.hadoop.hbase.io.ImmutableBytesWritable;
import org.apache.kylin.common.KylinConfig;
import org.apache.kylin.common.util.Bytes;
import org.apache.kylin.cube.CubeInstance;
import org.apache.kylin.cube.CubeManager;
import org.apache.kylin.cube.CubeSegment;
import org.apache.kylin.invertedindex.IIInstance;
import org.apache.kylin.invertedindex.IIManager;
import org.apache.kylin.invertedindex.IISegment;
import org.apache.kylin.metadata.model.SegmentStatusEnum;
import org.apache.kylin.metadata.realization.RealizationStatusEnum;
import org.apache.kylin.storage.hbase.HBaseConnection;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.common.collect.Lists;

/**
 */
public class DeployCoprocessorCLI {

    public static final String CubeObserverClass = "org.apache.kylin.storage.hbase.cube.v1.coprocessor.observer.AggregateRegionObserver";
    public static final String CubeEndpointClass = "org.apache.kylin.storage.hbase.cube.v2.coprocessor.endpoint.CubeVisitService";
    public static final String CubeObserverClassOld = "org.apache.kylin.storage.hbase.coprocessor.observer.AggregateRegionObserver";
    public static final String IIEndpointClassOld = "org.apache.kylin.storage.hbase.coprocessor.endpoint.IIEndpoint";
    public static final String IIEndpointClass = "org.apache.kylin.storage.hbase.ii.coprocessor.endpoint.IIEndpoint";
    private static final Logger logger = LoggerFactory.getLogger(DeployCoprocessorCLI.class);

    public static void main(String[] args) throws IOException {

        if (args == null || args.length <= 1) {
            printUsageAndExit();
        }

        KylinConfig kylinConfig = KylinConfig.getInstanceFromEnv();
        Configuration hconf = HBaseConnection.getCurrentHBaseConfiguration();
        FileSystem fileSystem = FileSystem.get(hconf);
        HBaseAdmin hbaseAdmin = new HBaseAdmin(hconf);

        String localCoprocessorJar;
        if ("default".equals(args[0])) {
            localCoprocessorJar = kylinConfig.getCoprocessorLocalJar();
        } else {
            localCoprocessorJar = new File(args[0]).getAbsolutePath();
        }

        logger.info("Identify coprocessor jar " + localCoprocessorJar);

        List<String> tableNames = getHTableNames(kylinConfig);
        logger.info("Identify tables " + tableNames);

        String filterType = args[1].toLowerCase();
        if (filterType.equals("-table")) {
            tableNames = filterByTables(tableNames, Arrays.asList(args).subList(2, args.length));
        } else if (filterType.equals("-cube")) {
            tableNames = filterByCubes(tableNames, Arrays.asList(args).subList(2, args.length));
        } else if (!filterType.equals("all")) {
            printUsageAndExit();
        }

        logger.info("Will execute tables " + tableNames);

        Set<String> oldJarPaths = getCoprocessorJarPaths(hbaseAdmin, tableNames);
        logger.info("Old coprocessor jar: " + oldJarPaths);

        Path hdfsCoprocessorJar = uploadCoprocessorJar(localCoprocessorJar, fileSystem, oldJarPaths);
        logger.info("New coprocessor jar: " + hdfsCoprocessorJar);

        List<String> processedTables = resetCoprocessorOnHTables(hbaseAdmin, hdfsCoprocessorJar, tableNames);

        // Don't remove old jars, missing coprocessor jar will fail hbase
        // removeOldJars(oldJarPaths, fileSystem);

        hbaseAdmin.close();

        logger.info("Processed " + processedTables);
        logger.info("Active coprocessor jar: " + hdfsCoprocessorJar);
    }

    private static void printUsageAndExit() {
        logger.info("Probe run, exiting. Append argument 'all' or specific tables/cubes to execute.");
        System.exit(0);
    }

    private static List<String> filterByCubes(List<String> allTableNames, List<String> cubeNames) {
        CubeManager cubeManager = CubeManager.getInstance(KylinConfig.getInstanceFromEnv());
        List<String> result = Lists.newArrayList();
        for (String c : cubeNames) {
            c = c.trim();
            if (c.endsWith(","))
                c = c.substring(0, c.length() - 1);

            CubeInstance cubeInstance = cubeManager.getCube(c);
            for (CubeSegment segment : cubeInstance.getSegments()) {
                String tableName = segment.getStorageLocationIdentifier();
                if (allTableNames.contains(tableName)) {
                    result.add(tableName);
                }
            }
        }
        return result;
    }

    private static List<String> filterByTables(List<String> allTableNames, List<String> tableNames) {
        List<String> result = Lists.newArrayList();
        for (String t : tableNames) {
            t = t.trim();
            if (t.endsWith(","))
                t = t.substring(0, t.length() - 1);

            if (allTableNames.contains(t)) {
                result.add(t);
            }
        }
        return result;
    }

    public static void deployCoprocessor(HTableDescriptor tableDesc) {
        try {
            initHTableCoprocessor(tableDesc);
            logger.info("hbase table " + tableDesc.getName() + " deployed with coprocessor.");

        } catch (Exception ex) {
            logger.error("Error deploying coprocessor on " + tableDesc.getName(), ex);
            logger.error("Will try creating the table without coprocessor.");
        }
    }

    private static void initHTableCoprocessor(HTableDescriptor desc) throws IOException {
        KylinConfig kylinConfig = KylinConfig.getInstanceFromEnv();
        Configuration hconf = HBaseConnection.getCurrentHBaseConfiguration();
        FileSystem fileSystem = FileSystem.get(hconf);

        String localCoprocessorJar = kylinConfig.getCoprocessorLocalJar();
        Path hdfsCoprocessorJar = DeployCoprocessorCLI.uploadCoprocessorJar(localCoprocessorJar, fileSystem, null);

        DeployCoprocessorCLI.addCoprocessorOnHTable(desc, hdfsCoprocessorJar);
    }

    public static void addCoprocessorOnHTable(HTableDescriptor desc, Path hdfsCoprocessorJar) throws IOException {
        logger.info("Add coprocessor on " + desc.getNameAsString());
        desc.addCoprocessor(IIEndpointClass, hdfsCoprocessorJar, 1000, null);
        desc.addCoprocessor(CubeEndpointClass, hdfsCoprocessorJar, 1001, null);
        desc.addCoprocessor(CubeObserverClass, hdfsCoprocessorJar, 1002, null);
    }

    public static void resetCoprocessor(String tableName, HBaseAdmin hbaseAdmin, Path hdfsCoprocessorJar) throws IOException {
        logger.info("Disable " + tableName);
        hbaseAdmin.disableTable(tableName);

        logger.info("Unset coprocessor on " + tableName);
        HTableDescriptor desc = hbaseAdmin.getTableDescriptor(TableName.valueOf(tableName));
        while (desc.hasCoprocessor(CubeObserverClass)) {
            desc.removeCoprocessor(CubeObserverClass);
        }
        while (desc.hasCoprocessor(CubeEndpointClass)) {
            desc.removeCoprocessor(CubeEndpointClass);
        }
        while (desc.hasCoprocessor(IIEndpointClass)) {
            desc.removeCoprocessor(IIEndpointClass);
        }
        // remove legacy coprocessor from v1.x
        while (desc.hasCoprocessor(CubeObserverClassOld)) {
            desc.removeCoprocessor(CubeObserverClassOld);
        }
        while (desc.hasCoprocessor(IIEndpointClassOld)) {
            desc.removeCoprocessor(IIEndpointClassOld);
        }
        addCoprocessorOnHTable(desc, hdfsCoprocessorJar);
        hbaseAdmin.modifyTable(tableName, desc);

        logger.info("Enable " + tableName);
        hbaseAdmin.enableTable(tableName);
    }

    private static List<String> resetCoprocessorOnHTables(HBaseAdmin hbaseAdmin, Path hdfsCoprocessorJar, List<String> tableNames) throws IOException {
        List<String> processed = new ArrayList<String>();

        for (String tableName : tableNames) {
            try {
                resetCoprocessor(tableName, hbaseAdmin, hdfsCoprocessorJar);
                processed.add(tableName);
            } catch (IOException ex) {
                logger.error("Error processing " + tableName, ex);
            }
        }
        return processed;
    }

    public static Path getNewestCoprocessorJar(KylinConfig config, FileSystem fileSystem) throws IOException {
        Path coprocessorDir = getCoprocessorHDFSDir(fileSystem, config);
        FileStatus newestJar = null;
        for (FileStatus fileStatus : fileSystem.listStatus(coprocessorDir)) {
            if (fileStatus.getPath().toString().endsWith(".jar")) {
                if (newestJar == null) {
                    newestJar = fileStatus;
                } else {
                    if (newestJar.getModificationTime() < fileStatus.getModificationTime())
                        newestJar = fileStatus;
                }
            }
        }
        if (newestJar == null)
            return null;

        Path path = newestJar.getPath().makeQualified(fileSystem.getUri(), null);
        logger.info("The newest coprocessor is " + path.toString());
        return path;
    }

    public static Path uploadCoprocessorJar(String localCoprocessorJar, FileSystem fileSystem, Set<String> oldJarPaths) throws IOException {
        Path uploadPath = null;
        File localCoprocessorFile = new File(localCoprocessorJar);

        // check existing jars
        if (oldJarPaths == null) {
            oldJarPaths = new HashSet<String>();
        }
        Path coprocessorDir = getCoprocessorHDFSDir(fileSystem, KylinConfig.getInstanceFromEnv());
        for (FileStatus fileStatus : fileSystem.listStatus(coprocessorDir)) {
            if (isSame(localCoprocessorFile, fileStatus)) {
                uploadPath = fileStatus.getPath();
                break;
            }
            String filename = fileStatus.getPath().toString();
            if (filename.endsWith(".jar")) {
                oldJarPaths.add(filename);
            }
        }

        // upload if not existing
        if (uploadPath == null) {
            // figure out a unique new jar file name
            Set<String> oldJarNames = new HashSet<String>();
            for (String path : oldJarPaths) {
                oldJarNames.add(new Path(path).getName());
            }
            String baseName = getBaseFileName(localCoprocessorJar);
            String newName = null;
            int i = 0;
            while (newName == null) {
                newName = baseName + "-" + (i++) + ".jar";
                if (oldJarNames.contains(newName))
                    newName = null;
            }

            // upload
            uploadPath = new Path(coprocessorDir, newName);
            FileInputStream in = null;
            FSDataOutputStream out = null;
            try {
                in = new FileInputStream(localCoprocessorFile);
                out = fileSystem.create(uploadPath);
                IOUtils.copy(in, out);
            } finally {
                IOUtils.closeQuietly(in);
                IOUtils.closeQuietly(out);
            }

            fileSystem.setTimes(uploadPath, localCoprocessorFile.lastModified(), -1);

        }

        uploadPath = uploadPath.makeQualified(fileSystem.getUri(), null);
        return uploadPath;
    }

    private static boolean isSame(File localCoprocessorFile, FileStatus fileStatus) {
        return fileStatus.getLen() == localCoprocessorFile.length() && fileStatus.getModificationTime() == localCoprocessorFile.lastModified();
    }

    private static String getBaseFileName(String localCoprocessorJar) {
        File localJar = new File(localCoprocessorJar);
        String baseName = localJar.getName();
        if (baseName.endsWith(".jar"))
            baseName = baseName.substring(0, baseName.length() - ".jar".length());
        return baseName;
    }

    private static Path getCoprocessorHDFSDir(FileSystem fileSystem, KylinConfig config) throws IOException {
        String hdfsWorkingDirectory = config.getHdfsWorkingDirectory();
        Path coprocessorDir = new Path(hdfsWorkingDirectory, "coprocessor");
        fileSystem.mkdirs(coprocessorDir);
        return coprocessorDir;
    }

    private static Set<String> getCoprocessorJarPaths(HBaseAdmin hbaseAdmin, List<String> tableNames) throws IOException {
        HashSet<String> result = new HashSet<String>();

        for (String tableName : tableNames) {
            HTableDescriptor tableDescriptor = null;
            try {
                tableDescriptor = hbaseAdmin.getTableDescriptor(TableName.valueOf(tableName));
            } catch (TableNotFoundException e) {
                logger.warn("Table not found " + tableName, e);
                continue;
            }

            Matcher keyMatcher;
            Matcher valueMatcher;
            for (Map.Entry<ImmutableBytesWritable, ImmutableBytesWritable> e : tableDescriptor.getValues().entrySet()) {
                keyMatcher = HConstants.CP_HTD_ATTR_KEY_PATTERN.matcher(Bytes.toString(e.getKey().get()));
                if (!keyMatcher.matches()) {
                    continue;
                }
                valueMatcher = HConstants.CP_HTD_ATTR_VALUE_PATTERN.matcher(Bytes.toString(e.getValue().get()));
                if (!valueMatcher.matches()) {
                    continue;
                }

                String jarPath = valueMatcher.group(1).trim();
                if (StringUtils.isNotEmpty(jarPath)) {
                    result.add(jarPath);
                }
            }
        }

        return result;
    }

    private static List<String> getHTableNames(KylinConfig config) {
        CubeManager cubeMgr = CubeManager.getInstance(config);

        ArrayList<String> result = new ArrayList<String>();
        for (CubeInstance cube : cubeMgr.listAllCubes()) {
            for (CubeSegment seg : cube.getSegments(SegmentStatusEnum.READY)) {
                String tableName = seg.getStorageLocationIdentifier();
                if (StringUtils.isBlank(tableName) == false) {
                    result.add(tableName);
                    System.out.println("added new table: " + tableName);
                }
            }
        }

        for (IIInstance ii : IIManager.getInstance(config).listAllIIs()) {
            if (ii.getStatus() == RealizationStatusEnum.READY) {
                for (IISegment seg : ii.getSegments()) {//streaming segment is never "READY"
                    String tableName = seg.getStorageLocationIdentifier();
                    if (StringUtils.isBlank(tableName) == false) {
                        result.add(tableName);
                        System.out.println("added new table: " + tableName);
                    }
                }
            }
        }

        return result;
    }
}
