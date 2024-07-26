<script setup>
import { NodeResizer } from '@vue-flow/node-resizer'
import { Handle, Position} from '@vue-flow/core'
import {initialize} from '../../js/initialize.js'
import { excelParser } from "../../js/excel-parser.js";
import { VDataTable } from 'vuetify/labs/components'

import Toolbar from './Toolbar.vue'

import {ref,onMounted} from 'vue'
import * as d3 from 'd3';

const props = defineProps({
  data: {
    type:Object,
    required: true
  },
  id: {
    type:String, 
    required: true
  },
  type: {
    type: String, 
    required: true
  }
})
const {cardWidth, cardHeight, resizeEndFunc} = initialize(props.data['width'], props.data['height'])
const scatterPlot = ref(null);

const sampleData = [
  { id: 1, x: 10, y: 20 },
  { id: 2, x: 30, y: 40 },
  { id: 3, x: 50, y: 60 },
];

const highlightNodeIds = [2];

onMounted(() => {
  drawScatterPlotWithHighlights(scatterPlot.value, props.data['input'], props.data['width'], props.data['height'],highlightNodeIds);
});

function drawScatterPlotWithHighlights(container, data, width, height, highlightIds) {
  console.log('dddd', data)
  const margin = { top: 10, right: 30, bottom: 30, left: 40 }
  width = width - margin.left - margin.right,
  height = height - margin.top - margin.bottom;

  const svg = d3.select(container)
    .append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)
  // const g =  svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)
    
  const x = d3.scaleLinear()
      .domain([ d3.min(data, d => d.tsne_x), d3.max(data, d => d.tsne_x)])
      .range([margin.left, width]);
    // svg.append('g').attr('transform', `translate(0,${height})`)
      // .call(d3.axisBottom(x));

  const y = d3.scaleLinear()
      .domain([d3.min(data, d => d.tsne_y), d3.max(data, d => d.tsne_y)])
      .range([height, margin.top]);
  // svg.append('g')
      // .call(d3.axisLeft(y));
  const tooltip = d3.select('body').append('div')
    .attr('id', 'tooltip')
    .style('position', 'absolute')
    .style('opacity', 0) // Start hidden
    .style('background', 'lightgrey') // Just an example styling
    .style('padding', '5px')
    .style('border-radius', '5px')
    .style('pointer-events', 'none'); // Make sure the tooltip doesn't interfere with mouse events
  
  const uniqueTypes = Array.from(new Set(data.map(d=>d['type'])))
  const colorMap = d3.scaleOrdinal()
  .domain(uniqueTypes) // Assuming 'type' is the property
  .range(d3.schemeCategory10); // Or any other range of colors

  const legend = svg.selectAll(".legend")
  .data(uniqueTypes)
  .enter().append("g")
  .attr("class", "legend")
  .attr("transform", (d, i) => `translate(0,${i * 20})`); // Stacking legend items vertically

legend.append("rect")
  .attr("x", width - 18) // Place it to the right; adjust as needed
  .attr("width", 18)
  .attr("height", 18)
  .style("fill", d=>colorMap(d));

legend.append("text")
  .attr("x", width - 24)
  .attr("y", 9)
  .attr("dy", ".35em")
  .style("text-anchor", "end")
  .text(d => {
    let delimiter = d.includes('#')? "#": "/";
    let parts = d.split(delimiter);
    return parts[parts.length-1]
  }); // Assuming the domain of your scale has the names for the legend


  svg.append('g')
    .selectAll('dot')
    .data(data)
    .enter()
    .append('circle')
      .attr('cx', d => x(d.tsne_x))
      .attr('cy', d => y(d.tsne_y))
      .attr('r', d=>d['r'])
      .attr('opacity', d=>d['opacity'])
      .attr('color', '#69b3a2')
      .style('fill', d=>colorMap(d.type))
      .on('mouseover', function(event, d){
        console.log(d)
        d3.select(this).attr('fill', 'red');
        tooltip
        .html(`Entity: ${d.text}`) // Set the tooltip content
        .style('left', `${event.pageX + 10}px`) // Offset a bit from cursor
        .style('top', `${event.pageY + 10}px`)
        .transition()
        .duration(200)
        .style('opacity', 1); // Make it visible
      })
      .on('mouseout', function(){
        d3.select(this).attr('fill', 'black'); // Revert color on hover out
      
        // Remove the tooltip
        tooltip.transition().duration(200).style('opacity', 0); // Hide tooltip
      })
}
</script>

<template>
    <div>
      <NodeResizer @resize="resizeEndFunc" min-width="100" min-height="30"  color="white"/>
      <Toolbar :data="data" :id="id" :type="type"></Toolbar>
      <!-- <tool-bar ></tool-bar> -->
      <Handle type="target" :position="Position.Left" />
      <Handle type="source" :position="Position.Right" />
      <v-card
      class="node-card"
      :width=cardWidth
      :height=cardHeight
      variant = "outlined"
      :title=type
      :style="{ backgroundColor: data.style['background'],
          borderColor: data.style['background'],
          borderRadius: data.style['borderRadius'], // Assuming the value is in pixels
          color: data.style['textColor']}">
      <div ref="scatterPlot">
      </div>
      </v-card>
      
    </div>
</template>
<style>

</style>