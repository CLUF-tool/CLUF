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

package org.apache.kylin.dict.lookup;

import java.io.DataInput;
import java.io.DataOutput;
import java.io.File;
import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.apache.commons.lang.ArrayUtils;
import org.apache.kylin.common.persistence.ResourceStore;
import org.apache.kylin.common.persistence.RootPersistentEntity;
import org.apache.kylin.dict.StringBytesConverter;
import org.apache.kylin.dict.TrieDictionary;
import org.apache.kylin.dict.TrieDictionaryBuilder;
import org.apache.kylin.dimension.Dictionary;
import org.apache.kylin.metadata.model.TableDesc;
import org.apache.kylin.source.ReadableTable;

import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.JsonAutoDetect.Visibility;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * @author yangli9
 */
@SuppressWarnings("serial")
@JsonAutoDetect(fieldVisibility = Visibility.NONE, getterVisibility = Visibility.NONE, isGetterVisibility = Visibility.NONE, setterVisibility = Visibility.NONE)
public class SnapshotTable extends RootPersistentEntity implements ReadableTable {

    @JsonProperty("signature")
    private TableSignature signature;
    @JsonProperty("useDictionary")
    private boolean useDictionary;

    private ArrayList<int[]> rowIndices;
    private Dictionary<String> dict;

    // default constructor for JSON serialization
    public SnapshotTable() {
    }

    SnapshotTable(ReadableTable table) throws IOException {
        this.signature = table.getSignature();
        this.useDictionary = true;
    }

    public void takeSnapshot(ReadableTable table, TableDesc tableDesc) throws IOException {
        this.signature = table.getSignature();

        int maxIndex = tableDesc.getMaxColumnIndex();

        TrieDictionaryBuilder<String> b = new TrieDictionaryBuilder<String>(new StringBytesConverter());

        TableReader reader = table.getReader();
        while (reader.next()) {
            String[] row = reader.getRow();
            if (row.length <= maxIndex) {
                throw new IllegalStateException("Bad hive table row, " + tableDesc + " expect " + (maxIndex + 1) + " columns, but got " + Arrays.toString(row));
            }

            for (String cell : row) {
                if (cell != null)
                    b.addValue(cell);
            }
        }

        this.dict = b.build(0);

        reader = table.getReader();
        ArrayList<int[]> allRowIndices = new ArrayList<int[]>();
        while (reader.next()) {
            String[] row = reader.getRow();
            int[] rowIndex = new int[row.length];
            for (int i = 0; i < row.length; i++) {
                rowIndex[i] = dict.getIdFromValue(row[i]);
            }
            allRowIndices.add(rowIndex);
        }
        this.rowIndices = allRowIndices;
    }

    public String getResourcePath() {
        return ResourceStore.SNAPSHOT_RESOURCE_ROOT + "/" + new File(signature.getPath()).getName() + "/" + uuid + ".snapshot";
    }

    public String getResourceDir() {
        return ResourceStore.SNAPSHOT_RESOURCE_ROOT + "/" + new File(signature.getPath()).getName();
    }

    @Override
    public TableReader getReader() throws IOException {
        return new TableReader() {

            int i = -1;

            @Override
            public boolean next() throws IOException {
                i++;
                return i < rowIndices.size();
            }

            @Override
            public String[] getRow() {
                int[] rowIndex = rowIndices.get(i);
                String[] row = new String[rowIndex.length];
                for (int x = 0; x < row.length; x++) {
                    row[x] = dict.getValueFromId(rowIndex[x]);
                }
                return row;
            }

            @Override
            public void close() throws IOException {
            }
        };
    }

    @Override
    public TableSignature getSignature() throws IOException {
        return signature;
    }

    /**
     * a naive implementation
     *
     * @return
     */
    @Override
    public int hashCode() {
        int[] parts = new int[this.rowIndices.size()];
        for (int i = 0; i < parts.length; ++i)
            parts[i] = Arrays.hashCode(this.rowIndices.get(i));
        return Arrays.hashCode(parts);
    }

    @Override
    public boolean equals(Object o) {
        if ((o instanceof SnapshotTable) == false)
            return false;
        SnapshotTable that = (SnapshotTable) o;

        //compare row by row
        if (this.rowIndices.size() != that.rowIndices.size())
            return false;
        for (int i = 0; i < this.rowIndices.size(); ++i) {
            if (!ArrayUtils.isEquals(this.rowIndices.get(i), that.rowIndices.get(i)))
                return false;
        }
        return true;
    }

    private static String NULL_STR;
    {
        try {
            // a special placeholder to indicate a NULL; 0, 9, 127, 255 are a few invisible ASCII characters
            NULL_STR = new String(new byte[] { 0, 9, 127, (byte) 255 }, "ISO-8859-1");
        } catch (UnsupportedEncodingException e) {
            // does not happen
        }
    }

    void writeData(DataOutput out) throws IOException {
        out.writeInt(rowIndices.size());
        if (rowIndices.size() > 0) {
            int n = rowIndices.get(0).length;
            out.writeInt(n);

            if (this.useDictionary == true) {
                dict.write(out);
                for (int i = 0; i < rowIndices.size(); i++) {
                    int[] row = rowIndices.get(i);
                    for (int j = 0; j < n; j++) {
                        out.writeInt(row[j]);
                    }
                }

            } else {
                for (int i = 0; i < rowIndices.size(); i++) {
                    int[] row = rowIndices.get(i);
                    for (int j = 0; j < n; j++) {
                        // NULL_STR is tricky, but we don't want to break the current snapshots
                        out.writeUTF(dict.getValueFromId(row[j]) == null ? NULL_STR : dict.getValueFromId(row[j]));
                    }
                }
            }
        }
    }

    void readData(DataInput in) throws IOException {
        int rowNum = in.readInt();
        if (rowNum > 0) {
            int n = in.readInt();
            rowIndices = new ArrayList<int[]>(rowNum);

            if (this.useDictionary == true) {
                this.dict = new TrieDictionary<String>();
                dict.readFields(in);

                for (int i = 0; i < rowNum; i++) {
                    int[] row = new int[n];
                    this.rowIndices.add(row);
                    for (int j = 0; j < n; j++) {
                        row[j] = in.readInt();
                    }
                }
            } else {
                List<String[]> rows = new ArrayList<String[]>(rowNum);
                TrieDictionaryBuilder<String> b = new TrieDictionaryBuilder<String>(new StringBytesConverter());

                for (int i = 0; i < rowNum; i++) {
                    String[] row = new String[n];
                    rows.add(row);
                    for (int j = 0; j < n; j++) {
                        row[j] = in.readUTF();
                        // NULL_STR is tricky, but we don't want to break the current snapshots
                        if (row[j].equals(NULL_STR))
                            row[j] = null;

                        b.addValue(row[j]);
                    }
                }
                this.dict = b.build(0);
                for (String[] row : rows) {
                    int[] rowIndex = new int[n];
                    for (int i = 0; i < n; i++) {
                        rowIndex[i] = dict.getIdFromValue(row[i]);
                    }
                    this.rowIndices.add(rowIndex);
                }
            }
        }
    }

}
