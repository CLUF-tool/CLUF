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

package org.apache.kylin.storage.hbase.common;

import static org.junit.Assert.assertEquals;

import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.apache.kylin.metadata.model.ColumnDesc;
import org.apache.kylin.metadata.model.TableDesc;
import org.apache.kylin.metadata.model.TblColRef;
import org.apache.kylin.storage.translate.FuzzyValueCombination;
import org.junit.Test;

import com.google.common.collect.Maps;

/**
 * @author yangli9
 * 
 */
public class FuzzyValueCombinationTest {

    static final TableDesc table = new TableDesc();
    static {
        table.setName("table");
        table.setDatabase("default");
    }
    static final TblColRef col1 = col(1, table);
    static final TblColRef col2 = col(2, table);
    static final TblColRef col3 = col(3, table);

    @Test
    public void testBasics() {
        System.out.println("test basics ============================================================================");
        Map<TblColRef, Set<String>> values = Maps.newHashMap();
        values.put(col1, set("a", "b", "c"));
        values.put(col2, set("x", "y", "z"));
        List<Map<TblColRef, String>> result = FuzzyValueCombination.calculate(values, 10);
        for (Map<TblColRef, String> item : result) {
            System.out.println(item);
        }
        assertEquals(9, result.size());
    }

    @Test
    public void testSomeNull() {
        System.out.println("test some null ============================================================================");
        Map<TblColRef, Set<String>> values = Maps.newHashMap();
        values.put(col1, set("a", "b", "c"));
        values.put(col2, set());
        values.put(col3, set("x", "y", "z"));
        List<Map<TblColRef, String>> result = FuzzyValueCombination.calculate(values, 10);
        for (Map<TblColRef, String> item : result) {
            System.out.println(item);
        }
        assertEquals(9, result.size());
    }

    @Test
    public void testAllNulls() {
        System.out.println("test all nulls ============================================================================");
        Map<TblColRef, Set<String>> values = Maps.newHashMap();
        values.put(col1, set());
        values.put(col2, set());
        values.put(col3, set());
        List<Map<TblColRef, String>> result = FuzzyValueCombination.calculate(values, 10);
        for (Map<TblColRef, String> item : result) {
            System.out.println(item);
        }
        assertEquals(0, result.size());
    }

    @Test
    public void testCap() {
        System.out.println("test cap ============================================================================");
        Map<TblColRef, Set<String>> values = Maps.newHashMap();
        values.put(col1, set("1", "2", "3", "4"));
        values.put(col2, set("a", "b", "c"));
        values.put(col3, set("x", "y", "z"));
        List<Map<TblColRef, String>> result = FuzzyValueCombination.calculate(values, 10);
        for (Map<TblColRef, String> item : result) {
            System.out.println(item);
        }
        assertEquals(0, result.size());
    }

    private static TblColRef col(int i, TableDesc t) {
        ColumnDesc col = ColumnDesc.mockup(t, i, "Col" + i, "string");
        return new TblColRef(col);
    }

    private Set<String> set(String... values) {
        return new HashSet<String>(Arrays.asList(values));
    }
}
