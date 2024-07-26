<template>
  <div class="jumbotron vertical-center">
    <div class="container">
      <Toolbar :data="data" :id="id" :type="type"></Toolbar>
      <NodeResizer @resize="resizeEndFunc" min-width="100" min-height="30" color="white"/>
      <Handle type="target" :position="Position.Left" />
      <Handle type="source" :position="Position.Right" />
      <link
        rel="stylesheet"
        href="https://cdn.jsdelivr.net/npm/bootswatch@4.5.2/dist/flatly/bootstrap.min.css"
        integrity="sha384-qF/QmIAj5ZaYFAeQcrQ6bfVMAh4zZlrGwTPY7T/M+iTTLJqJBJjwwnsE5Y0mV7QK"
        crossorigin="anonymous"
      />
      <div class="card-header">
        Graph Viewer
      </div>
      <div class="card-body">
        <div ref="subgraph" class="graph"></div>
      </div>
      <div class="input-group mt-6">
        <textarea v-model="nodeId" placeholder="Enter Node ID" class="form-control"></textarea>
        <button @click="displaySubgraph" class="btn btn-primary">Display Node</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import * as d3 from 'd3';
import { Handle, Position } from '@vue-flow/core';
import { NodeResizer } from '@vue-flow/node-resizer';
import Toolbar from './Toolbar.vue';
import * as XLSX from 'xlsx';

const nodeId = ref('');
const subgraph = ref(null);
const graphData = ref([]);

const props = defineProps({
  data: Object,
  id: String,
  type: String
});

watch(() => props.data.input, (newData, oldData) => {
  if (newData && newData !== oldData) {
    console.log('New data received:', newData);
    graphData.value = {
      nodes: newData,
      edges: []
    };
    console.log('Graph data after initialization:', graphData.value);
    drawGraph(graphData.value, subgraph.value);
  }
});



function drawGraph(data, container) {
  if (!data || !container) return;

  d3.select(container).selectAll("*").remove();

  const width = 700;
  const height = 700;
  const svg = d3.select(container)
    .append("svg")
    .attr("width", width)
    .attr("height", height);

  // Ensure data.nodes is an array
  const nodes = Array.isArray(data.nodes) ? data.nodes : Object.values(data.nodes || {});
  const edges = data.edges || [];

  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(edges).id(d => d.id).distance(150))
    .force("charge", d3.forceManyBody().strength(-500))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(50));

  // Draw edges
  const link = svg.append("g")
    .selectAll("line")
    .data(edges)
    .enter().append("line")
    .attr("stroke", "#999")
    .attr("stroke-opacity", 0.6)
    .attr("stroke-width", 2)
    .attr("marker-end", "url(#arrowhead)");

  // Draw edge labels
  const edgeLabels = svg.append("g")
    .selectAll("text")
    .data(edges)
    .enter().append("text")
    .attr("font-size", "10px")
    .attr("text-anchor", "middle")
    .text(d => d.label);

  // Draw nodes
  console.log('Data used for drawing:', JSON.parse(JSON.stringify(data)));

  const nodeGroup = svg.selectAll(".node")
    .data(data.nodes)
    .enter().append("g")
    .attr("class", "node")
    .call(d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended));

  console.log('Nodes being created:', data.nodes);

  nodeGroup.append("circle")
    .attr("r", 40)
    .attr("fill", "#69b3a2")
    .on("mouseover", showNodeInfo)
    .on("mouseout", hideNodeInfo)
    .on("click", showPieChart);

  nodeGroup.append("text")
    .attr("text-anchor", "middle")
    .attr("dy", ".35em")
    .text(d => d.label);

  // Add arrowhead marker for directed edges
  svg.append("defs").append("marker")
    .attr("id", "arrowhead")
    .attr("viewBox", "-0 -5 10 10")
    .attr("refX", 45)
    .attr("refY", 0)
    .attr("orient", "auto")
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("xoverflow", "visible")
    .append("svg:path")
    .attr("d", "M 0,-5 L 10 ,0 L 0,5")
    .attr("fill", "#999")
    .style("stroke", "none");

  simulation.on("tick", () => {
    link
      .attr("x1", d => d.source.x)
      .attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x)
      .attr("y2", d => d.target.y);

    edgeLabels
      .attr("x", d => (d.source.x + d.target.x) / 2)
      .attr("y", d => (d.source.y + d.target.y) / 2);

    nodeGroup.attr("transform", d => `translate(${d.x},${d.y})`);
  });
  
  
  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }

  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }

  function showNodeInfo(event, d) {
    const tooltip = d3.select("body").append("div")
      .attr("class", "tooltip")
      .style("position", "absolute")
      .style("background-color", "white")
      .style("border", "1px solid #ddd")
      .style("padding", "10px")
      .style("opacity", 0);

    let content = "<strong>Node Info:</strong><br>";
    for (const [key, value] of Object.entries(d)) {
      if (key !== "x" && key !== "y" && key !== "vx" && key !== "vy" && key !== "index") {
        content += `${key}: ${value}<br>`;
      }
    }

    tooltip.html(content)
      .style("left", (event.pageX + 10) + "px")
      .style("top", (event.pageY - 10) + "px")
      .transition()
      .duration(200)
      .style("opacity", .9);
  }

  function hideNodeInfo() {
    d3.select(".tooltip").remove();
  }

  function showPieChart(event, d) {
    event.stopPropagation();
    const currentNode = d3.select(this.parentNode);
    const existingPie = currentNode.select(".pie-chart");

    //Update nodeId.value with the clicked node's label
  nodeId.value = d.label;
  console.log('Updated nodeId.value:', nodeId.value);


    if (!existingPie.empty()) {
      existingPie.remove();
      return;
    }

    const pieChartData = [
      { label: "Action 1", value: 50 },
      { label: "Action 3", value: 50 }
    ];

    const radius = 70;
    const pie = d3.pie().value(d => d.value);
    const arc = d3.arc().innerRadius(radius - 30).outerRadius(radius);

    const customColors = ['rgba(246, 186, 156, 0.7)', 'rgba(156, 220, 246, 0.7)']; // Added alpha channel for transparency


    const pieGroup = currentNode.append("g")
      .attr("class", "pie-chart");

    pieGroup.selectAll("path")
      .data(pie(pieChartData))
      .enter().append("path")
      .attr("d", arc)
      .attr("fill", (d, i) => customColors[i % customColors.length])
      .on("click", (event, d) => {
        event.stopPropagation();
        handlePieClick(d, event.currentTarget);
      });
  }
}

const drawSingleNode = (nodeId, container) => {
  d3.select(container).selectAll('*').remove();

  if (nodeId) {
    const width = 800;
    const height = 800;
    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height);

    const nodeX = width / 2;
    const nodeY = height / 2;

    const nodeGroup = svg.append("g")
      .attr("class", "node")
      .attr("transform", `translate(${nodeX},${nodeY})`);

    nodeGroup.append('circle')
      .attr('r', 40)
      .attr('fill', '#69b3a2')
      .on("mouseover", showNodeInfo)
      .on("mouseout", hideNodeInfo)
      .on("click", showPieChart);

    nodeGroup.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '.35em')
      .text(nodeId);

    function showNodeInfo(event, d) {
      const tooltip = d3.select("body").append("div")
        .attr("class", "tooltip")
        .style("position", "absolute")
        .style("background-color", "white")
        .style("border", "1px solid #ddd")
        .style("padding", "10px")
        .style("opacity", 0);

      let content = "<strong>Node Info:</strong><br>";
      content += `ID: ${nodeId}<br>`;

      tooltip.html(content)
        .style("left", (event.pageX + 10) + "px")
        .style("top", (event.pageY - 10) + "px")
        .transition()
        .duration(200)
        .style("opacity", .9);
    }

    function hideNodeInfo() {
      d3.select(".tooltip").remove();
    }

    function showPieChart(event) {
      event.stopPropagation();
      const existingPie = nodeGroup.select(".pie-chart");

      if (!existingPie.empty()) {
        existingPie.remove();
        return;
      }

      const pieChartData = [
        { label: 'Action 1', value: 50 },
        { label: 'Action 3', value: 50 }
      ];

      const radius = 70;
      const pie = d3.pie().value(d => d.value);
      const arc = d3.arc().innerRadius(radius - 30).outerRadius(radius);

      const customColors = ['rgba(246, 186, 156, 0.8)', 'rgba(156, 220, 246, 0.8)'];


      const pieGroup = nodeGroup.append("g")
        .attr("class", "pie-chart");

      pieGroup.selectAll("path")
        .data(pie(pieChartData))
        .enter().append("path")
        .attr("d", arc)
        .attr("fill", (d, i) => customColors[i % customColors.length])
        .on("click", (event, d) => {
          event.stopPropagation();
          handlePieClick(d, event.currentTarget);
        });
    }
  }
};

const handlePieClick = async (pieData, element) => {
  const toyData = [
    { Resource_start: "FMMP Important Farmland Maps", Resource_end: "Wildlife Movement Barrier Priorities", table_name: "in_dataset" },
    { Resource_start: "FMMP Important Farmland Maps", Resource_end: "Land Use Change Probability - 2100", table_name: "test_link" },
    { Resource_start: "Wildlife Movement Barrier Priorities", Resource_end: "C-CAP Regional Land Cover and Change", table_name: "for_testing" }
  ];

  console.log('Clicked pie section:', pieData);
  console.log('nodeId.value:', nodeId.value);
  const currentNodeLabel = nodeId.value;
  console.log('currentNodeLabel:', currentNodeLabel);

  if (pieData.data.label === 'Action 3') {
    const connectedNodes = toyData.filter(row => row.Resource_start === currentNodeLabel);

    if (connectedNodes.length > 0) {
      const newEdges = connectedNodes.map(row => ({
        source: graphData.value.nodes.find(n => n.label === row.Resource_start).id,
        target: row.Resource_end,
        label: row.table_name
      }));

      // Ensure graphData.value has the correct structure
      if (!graphData.value.edges) {
        graphData.value.edges = [];
      }

      // Add new edges
      graphData.value.edges = [...graphData.value.edges, ...newEdges];

      // Ensure all nodes exist
      const allNodeIds = new Set([
        ...graphData.value.nodes.map(n => n.id),
        ...newEdges.map(e => e.target)
      ]);

      graphData.value.nodes = Array.from(allNodeIds).map(id => {
        const existingNode = graphData.value.nodes.find(n => n.id === id);
        return existingNode || { id, label: id };
      });

      console.log('Nodes after update:', graphData.value.nodes);
      console.log('Edges after update:', graphData.value.edges);

      // Draw the updated graph
      drawGraph(graphData.value, subgraph.value);
    } else {
      console.log('No connections found for the current node:', currentNodeLabel);
    }
  
  
  } else if (pieData.data.label === 'Action 1') {
    console.log('Clicked action:', pieData.data.label);
    if (currentNodeLabel) {
      const nodeIdToRemove = findNodeIdByLabel(currentNodeLabel);
      console.log('Node ID to remove:', nodeIdToRemove);
      if (nodeIdToRemove) {
        const subgraphData = graphData.value.filter(node => node.id !== nodeIdToRemove);
        drawGraph(subgraphData, subgraph.value);
      } else {
        console.log(`Node with label '${currentNodeLabel}' not found.`);
      }
    } else {
      console.log('No node selected.');
    }
  } else {
    console.log('No action for this pie section.');
  }
};



const findNodeIdByLabel = (label) => {
  const node = graphData.value.find(node => node.label === label);
  if (node) {
    console.log(`Found node with label '${label}':`, node);
    console.log(`Node ID to remove: ${node.id}`);
    return node.id;
  } else {
    console.log(`Node with label '${label}' not found.`);
    return null;
  }
};



const displaySubgraph = () => {
  const id = nodeId.value.trim();
  if (id) {
    drawSingleNode(id, subgraph.value);
  } else {
    console.error('Node ID cannot be empty.');
  }
};
</script>

<style scoped>
.graph {
  width: 100%;
}
.tooltip {
  position: absolute;
  background-color: white;
  border: 1px solid #ddd;
  padding: 10px;
  pointer-events: none;
}
</style>