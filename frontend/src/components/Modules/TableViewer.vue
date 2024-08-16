<script setup>
import { NodeResizer } from '@vue-flow/node-resizer'
import { Handle, Position } from '@vue-flow/core'
import { initialize } from '../../js/initialize.js'
import { excelParser } from "../../js/excel-parser.js";
import { VDataTable } from 'vuetify/labs/components'
import { TabulatorFull as Tabulator } from 'tabulator-tables'; 
import { ref, reactive, onMounted, watch, toRaw } from 'vue';
import Toolbar from './Toolbar.vue'
import * as XLSX from 'xlsx';

const { cardWidth, cardHeight, resizeEndFunc } = initialize(props.data['width'], props.data['height']);

const props = defineProps({
  data: {
    type: Object,
    required: true
  },
  id: {
    type: String, 
    required: true
  },
  type: {
    type: String, 
    required: true
  }
});

const table = ref(null);
const tabulator = ref(null);
const tab = ref('one');
const selectedRows = ref([]);
const parsedData = ref({});
const tabs = ref([]);

const handleFileUpload = (event) => {
  const file = event.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const workbook = XLSX.read(e.target.result, { type: 'binary' });
      const sheets = workbook.SheetNames;
      const tempParsedData = {};

      sheets.forEach(sheetName => {
        const worksheet = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName], { header: 1 });
        const headers = worksheet[0];
        const data = worksheet.slice(1).map(row => {
          const rowData = {};
          headers.forEach((header, index) => {
            let cellValue = row[index];
            // Check if the cellValue is a number and within the Excel date range
            if (typeof cellValue === 'number' && cellValue > 25569) {
              // Convert Excel date serial number to JavaScript date
              const date = new Date((cellValue - 25569) * 86400 * 1000);
              // Format the date as needed, e.g., YYYY/MM/DD
              cellValue = date.toISOString().split('T')[0];
            }
            rowData[header] = cellValue;
          });
          return rowData;
        });

        tempParsedData[sheetName] = { data, headers };
        props.data.output = data;
      });

      parsedData.value = tempParsedData;
      initializeTabulator(parsedData.value);
      console.log(parsedData.value);
    };
    reader.readAsBinaryString(file);
  }
};

const initializeTabulator = (parsedDataValue) => {
  try {
    const firstSheet = Object.keys(parsedDataValue)[0];
    tabulator.value = new Tabulator(table.value, {
      layout: "fitColumns",
      responsiveLayout: "collapse",
      movableColumns: false,
      resizableColumns: true,
      selectable: true,
      rowSelection: "checkbox",
      reactiveData: true,
      columns: parsedDataValue[firstSheet].headers.map(header => ({ title: header, field: header })),
      data: parsedDataValue[firstSheet].data,
      rowSelected: (row) => {
        console.log('Row Selected:', row.getData());
      },
      rowDeselected: (row) => {
        console.log('Row Deselected:', row.getData());
      }
    });

    tabs.value = Object.keys(parsedDataValue);
    console.log('Tabulator initialized with data:', parsedDataValue);
  } catch (error) {
    console.error('Error initializing Tabulator:', error);
  }
};

const getSelectedRows = () => {
  if (tabulator.value) {
    const selectedRowsData = tabulator.value.getSelectedData();
    console.log('Selected Rows:', selectedRowsData);
    selectedRows.value = selectedRowsData;
  }
};

const switchTab = (sheetName) => {
  if (parsedData.value[sheetName]) {
    const { data, headers } = parsedData.value[sheetName];
    if (tabulator.value) {
      tabulator.value.setColumns(headers.map(header => ({ title: header, field: header })));
      tabulator.value.setData(data);
    } else {
      console.error('Tabulator instance not initialized');
    }
  } else {
    console.error('Sheet not found:', sheetName);
  }
};

onMounted(() => {
  if (!tabulator.value) {
    tabulator.value = new Tabulator(table.value, {
      data: [],
      columns: [],
      layout: "fitColumns",
      responsiveLayout: "collapse",
      movableColumns: false,
      resizableColumns: true,
      selectable: true,
      rowSelection: "checkbox",
    });
  }
});

watch(selectedRows, (newSelectedRows) => {
  if (newSelectedRows.length > 0) {
    props['data']['output'] = newSelectedRows;
  } else {
    props['data']['output'] = toRaw(tabulator.value.getData());
  }
}, { deep: true });

watch(() => props['data']['input'], (newData) => {
  if (Array.isArray(newData) && newData.length > 0 && typeof newData[0] === 'object') {
    const temp = toRaw(newData);
    const columns = Object.keys(temp[0]).map(column => ({ title: column, field: column }));
    if (tabulator.value) {
      tabulator.value.setColumns(columns);
      tabulator.value.setData(temp).then(() => {
        console.log('Data updated');
      }).catch(error => {
        console.error('Error updating data:', error);
      });
    }
    props['data']['output'] = newData;
  } else {
    if (tabulator.value) {
      tabulator.value.setData([]);
      tabulator.value.redraw(true);
    } else {
      tabulator.value = new Tabulator(table.value, {
        data: [],
        reactiveData: true,
      });
    }
  }
}, { deep: true });

const sortField = ref('Name');
const sortDirection = ref('Asc');
const fieldOptions = ['Name', 'Age', 'FavouriteColor', 'Dob'];
const directionOptions = ['Asc', 'Desc'];

function triggerSort() {
  tabulator.value.setSort(sortField.value, sortDirection.value);
}

const filterField = ref('Column Name');
const filterValue = ref('');

function applyFilter() {
  tabulator.value.setFilter(filterField.value, 'like', filterValue.value);
}

function clearFilter() {
  tabulator.value.clearFilter();
}
</script>

<template>
  <div>
    <NodeResizer @resize="resizeEndFunc" min-width="100" min-height="30" color="white"/>
    <Toolbar :data="data" :id="id" :type="type"></Toolbar>
    <Handle type="target" :position="Position.Left" />
    <Handle type="source" :position="Position.Right" />

    <!-- File Input for Excel Upload -->
    <input type="file" @change="handleFileUpload" accept=".xlsx, .xls" style="margin-bottom: 20px;" />

    <v-card
      :width="cardWidth"
      :height="cardHeight"
      variant="outlined"
      :title="'Table Viewer'"
      :style="{ backgroundColor: data.style['background'],
          borderColor: data.style['background'],
          borderRadius: data.style['borderRadius'], 
          color: data.style['textColor']}"
    >
      <div>
        <div v-if="tabs.length > 0">
          <v-tabs v-model="tab">
            <v-tab v-for="sheetName in tabs" :key="sheetName" @click="switchTab(sheetName)">
              {{ sheetName }}
            </v-tab>
          </v-tabs>
        </div>
        <div class="table-container">
          <div ref="table"></div>
        </div>
        <v-btn @click="getSelectedRows">Get Selected Rows</v-btn>
      </div>
    </v-card>
  </div>
</template>


<style>
  .filter-button-col {
    margin-left: -80px;
  }
  .custom-tab {
    min-width: 60px;
    max-width: 120px;
    text-align: center;
  }
  .table-container {
    max-height: 400px; /* Adjust the height as needed */
    overflow-y: auto;
    overflow-x: auto;
  }
</style>
