# How to add new template? 
1. template vue in Modules  e.g. TableViewer.vue
2. main.vue add import e.g. import TableViewerNode from './TableViewer.vue'
3. main.vue add template. 
 <template #node-tableViewer="{data,id,type}">
                <TableViewerNode :data="data" :id="id" :type="type"></TableViewerNode>
              </template>

4. SideBar.vue
5. NewNode.vue is made for testing purposes of creating a new node
   
