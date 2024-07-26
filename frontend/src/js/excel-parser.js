import Papa from 'papaparse';

export const excelParser = () => {
 function parseCSV(csvData) {
    const parsedData = Papa.parse(csvData, {
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true,
    });

    // Extract column names from the first row of the parsed data
    const columnNames = parsedData.meta.fields;

    return {
      data: parsedData.data,
      columns: columnNames.map(name => ({ title: name, field: name })),
    };
 }

 return {
    parseCSV,
 };
};
