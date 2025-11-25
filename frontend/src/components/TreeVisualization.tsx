import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { TreeNode } from '../types';

interface TreeVisualizationProps {
  data: TreeNode;
  onNodeClick?: (node: TreeNode) => void;
}

export default function TreeVisualization({ data, onNodeClick }: TreeVisualizationProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: Math.max(600, containerRef.current.clientWidth * 0.6),
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  useEffect(() => {
    if (!svgRef.current || !data || dimensions.width === 0) return;

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove();

    const margin = { top: 20, right: 120, bottom: 20, left: 120 };
    const width = dimensions.width - margin.left - margin.right;
    const height = dimensions.height - margin.top - margin.bottom;

    // Create SVG
    const svg = d3
      .select(svgRef.current)
      .attr('width', dimensions.width)
      .attr('height', dimensions.height);

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Create tree layout
    const treeLayout = d3.tree<TreeNode>().size([height, width]);

    // Convert data to hierarchy
    const root = d3.hierarchy(data);
    const treeData = treeLayout(root);

    // Add links
    g.selectAll('.link')
      .data(treeData.links())
      .enter()
      .append('path')
      .attr('class', 'link')
      .attr('fill', 'none')
      .attr('stroke', '#94a3b8')
      .attr('stroke-width', 2)
      .attr(
        'd',
        d3
          .linkHorizontal<any, any>()
          .x((d) => d.y)
          .y((d) => d.x)
      );

    // Add nodes
    const nodes = g
      .selectAll('.node')
      .data(treeData.descendants())
      .enter()
      .append('g')
      .attr('class', 'node')
      .attr('transform', (d) => `translate(${d.y},${d.x})`)
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        if (onNodeClick) {
          onNodeClick(d.data);
        }
      });

    // Add circles for nodes
    nodes
      .append('circle')
      .attr('r', 8)
      .attr('fill', (d) => {
        const health = d.data.health_score;
        if (health === null) return '#94a3b8';
        if (health >= 75) return '#22c55e';
        if (health >= 50) return '#eab308';
        if (health >= 25) return '#f97316';
        return '#ef4444';
      })
      .attr('stroke', (d) => {
        const status = d.data.status;
        if (status === 'banned') return '#dc2626';
        if (status === 'flagged') return '#eab308';
        if (status === 'suspended') return '#f97316';
        return '#22c55e';
      })
      .attr('stroke-width', 3);

    // Add labels
    nodes
      .append('text')
      .attr('dy', '.35em')
      .attr('x', (d) => (d.children ? -13 : 13))
      .attr('text-anchor', (d) => (d.children ? 'end' : 'start'))
      .text((d) => d.data.username)
      .attr('font-size', '12px')
      .attr('fill', '#1f2937')
      .attr('class', 'dark:fill-white');

    // Add health score labels
    nodes
      .filter((d) => d.data.health_score !== null)
      .append('text')
      .attr('dy', '1.8em')
      .attr('x', (d) => (d.children ? -13 : 13))
      .attr('text-anchor', (d) => (d.children ? 'end' : 'start'))
      .text((d) => `${d.data.health_score?.toFixed(0)}%`)
      .attr('font-size', '10px')
      .attr('fill', '#6b7280')
      .attr('class', 'dark:fill-gray-400');
  }, [data, dimensions, onNodeClick]);

  return (
    <div ref={containerRef} className="w-full">
      <svg ref={svgRef} className="w-full" />
      
      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-green-500" />
          <span className="text-gray-700 dark:text-gray-300">Health: 75-100%</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-yellow-500" />
          <span className="text-gray-700 dark:text-gray-300">Health: 50-74%</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-orange-500" />
          <span className="text-gray-700 dark:text-gray-300">Health: 25-49%</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-red-500" />
          <span className="text-gray-700 dark:text-gray-300">Health: 0-24%</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-gray-400" />
          <span className="text-gray-700 dark:text-gray-300">No health data</span>
        </div>
      </div>
    </div>
  );
}

