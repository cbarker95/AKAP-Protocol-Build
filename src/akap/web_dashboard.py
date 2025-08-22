"""
AKAP Web Dashboard
Interactive visualization for knowledge patterns, insights, and federation
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from flask import Flask, render_template_string, jsonify, request, send_from_directory
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import networkx as nx
from datetime import datetime, timedelta
import threading
import webbrowser
from pathlib import Path

logger = logging.getLogger(__name__)

class AKAPDashboard:
    """
    Web-based dashboard for AKAP Protocol visualization and management
    
    Features:
    - Interactive knowledge graph visualization
    - Pattern analysis charts and insights
    - Performance monitoring
    - Federation status and peer management
    - Real-time semantic search interface
    - Export capabilities for insights and data
    """
    
    def __init__(self, knowledge_node, host: str = "127.0.0.1", port: int = 5000):
        self.knowledge_node = knowledge_node
        self.host = host
        self.port = port
        
        # Flask app setup
        self.app = Flask(__name__, 
                        static_folder=None,
                        template_folder=None)
        self.setup_routes()
        
        # Dashboard state
        self.is_running = False
        self.server_thread = None
        
        logger.info(f"AKAP Dashboard initialized on {host}:{port}")
    
    def setup_routes(self):
        """Setup Flask routes for the dashboard"""
        
        @self.app.route('/')
        def dashboard_home():
            return render_template_string(self.get_dashboard_html())
        
        @self.app.route('/api/stats')
        def api_stats():
            """Get knowledge base statistics"""
            stats = self.knowledge_node.get_graph_stats()
            
            # Add performance data if available
            if hasattr(self.knowledge_node, 'performance_optimizer'):
                perf_report = self.knowledge_node.performance_optimizer.get_performance_report()
                stats['performance'] = perf_report
            
            return jsonify(stats)
        
        @self.app.route('/api/graph')
        def api_graph():
            """Get knowledge graph data for visualization"""
            return jsonify(self.get_graph_data())
        
        @self.app.route('/api/patterns')
        def api_patterns():
            """Get pattern analysis data"""
            if self.knowledge_node.pattern_extractor:
                patterns = self.knowledge_node.extract_patterns()
                return jsonify(patterns)
            return jsonify({"error": "Pattern extractor not available"})
        
        @self.app.route('/api/search', methods=['POST'])
        def api_search():
            """Perform semantic search"""
            data = request.get_json()
            query = data.get('query', '')
            
            if not query:
                return jsonify({"error": "Query required"})
            
            results = self.knowledge_node.semantic_search(query, top_k=10)
            return jsonify({"results": results})
        
        @self.app.route('/api/insights')
        def api_insights():
            """Get generated insights"""
            if self.knowledge_node.pattern_extractor:
                insights = self.knowledge_node.get_insights(max_insights=5)
                return jsonify({"insights": insights})
            return jsonify({"insights": []})
        
        @self.app.route('/api/federation')
        def api_federation():
            """Get federation status"""
            if hasattr(self.knowledge_node, 'federation_protocol'):
                federation_stats = self.knowledge_node.federation_protocol.get_federation_stats()
                return jsonify(federation_stats)
            return jsonify({"federation_enabled": False})
        
        @self.app.route('/api/themes')
        def api_themes():
            """Get document themes visualization data"""
            return jsonify(self.get_themes_chart())
    
    def get_graph_data(self) -> Dict[str, Any]:
        """Convert NetworkX graph to format suitable for web visualization"""
        
        if not self.knowledge_node.graph or self.knowledge_node.graph.number_of_nodes() == 0:
            return {"nodes": [], "edges": []}
        
        # Convert nodes
        nodes = []
        for node_id, node_data in self.knowledge_node.graph.nodes(data=True):
            node_type = node_data.get('type', 'unknown')
            
            nodes.append({
                'id': str(node_id),
                'label': str(node_id)[:50],  # Truncate long labels
                'type': node_type,
                'size': self.knowledge_node.graph.degree(node_id) * 2 + 5,  # Size based on connections
                'color': self._get_node_color(node_type),
                'concepts': node_data.get('concepts', [])[:10]  # Limit concepts for performance
            })
        
        # Convert edges  
        edges = []
        for source, target, edge_data in self.knowledge_node.graph.edges(data=True):
            edges.append({
                'source': str(source),
                'target': str(target), 
                'relationship': edge_data.get('relationship', 'related'),
                'weight': edge_data.get('weight', 1)
            })
        
        return {
            'nodes': nodes[:500],  # Limit for performance
            'edges': edges[:1000],  # Limit for performance
            'stats': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'displayed_nodes': min(len(nodes), 500),
                'displayed_edges': min(len(edges), 1000)
            }
        }
    
    def _get_node_color(self, node_type: str) -> str:
        """Get color for node based on type"""
        colors = {
            'document': '#4CAF50',  # Green for documents
            'concept': '#2196F3',   # Blue for concepts
            'theme': '#FF9800',     # Orange for themes
            'unknown': '#9E9E9E'    # Gray for unknown
        }
        return colors.get(node_type, colors['unknown'])
    
    def get_themes_chart(self) -> Dict[str, Any]:
        """Create themes visualization data"""
        
        if not self.knowledge_node.pattern_extractor:
            return {"error": "Pattern extractor not available"}
        
        themes = self.knowledge_node.get_themes()
        
        if not themes:
            return {"labels": [], "values": [], "title": "No themes available"}
        
        # Prepare data for pie chart
        labels = list(themes.keys())[:10]  # Top 10 themes
        values = [len(docs) for docs in themes.values()][:10]
        
        return {
            "labels": labels,
            "values": values,
            "title": "Document Distribution by Theme",
            "total_themes": len(themes)
        }
    
    def get_dashboard_html(self) -> str:
        """Generate the HTML for the dashboard"""
        
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AKAP Protocol Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .full-width { grid-column: span 2; }
        .panel { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .stat-card { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .stat-value { font-size: 2em; font-weight: bold; color: #667eea; }
        .search-box { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 15px; }
        .insight-item { background: #e3f2fd; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #2196F3; }
        .loading { text-align: center; color: #666; font-style: italic; }
        #knowledge-graph { height: 500px; border: 1px solid #ddd; border-radius: 8px; }
        .btn { background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        .btn:hover { background: #5a6fd8; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 AKAP Protocol Dashboard</h1>
        <p>Knowledge sovereignty through AI-assisted collective intelligence</p>
    </div>
    
    <div class="container">
        <div class="panel">
            <h3>📊 Knowledge Base Statistics</h3>
            <div class="stats-grid" id="stats-grid">
                <div class="loading">Loading statistics...</div>
            </div>
        </div>
        
        <div class="panel">
            <h3>🔍 Semantic Search</h3>
            <input type="text" id="search-query" class="search-box" placeholder="Enter your search query...">
            <button class="btn" onclick="performSearch()">Search</button>
            <div id="search-results"></div>
        </div>
        
        <div class="panel full-width">
            <h3>🕸️ Knowledge Graph Visualization</h3>
            <div id="knowledge-graph"></div>
        </div>
        
        <div class="panel">
            <h3>🎨 Document Themes</h3>
            <div id="themes-chart"></div>
        </div>
        
        <div class="panel">
            <h3>💡 AI-Generated Insights</h3>
            <div id="insights-container">
                <div class="loading">Loading insights...</div>
            </div>
        </div>
    </div>

    <script>
        // Global data
        let graphData = null;
        
        // Load dashboard data
        async function loadDashboard() {
            await Promise.all([
                loadStats(),
                loadGraph(),
                loadThemes(),
                loadInsights()
            ]);
        }
        
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                
                const statsHtml = `
                    <div class="stat-card">
                        <div class="stat-value">${data.documents || 0}</div>
                        <div>Documents</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${data.concepts || 0}</div>
                        <div>Concepts</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${data.total_edges || 0}</div>
                        <div>Connections</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${data.semantic_search?.total_embeddings || 0}</div>
                        <div>Embeddings</div>
                    </div>
                `;
                
                document.getElementById('stats-grid').innerHTML = statsHtml;
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }
        
        async function loadGraph() {
            try {
                const response = await fetch('/api/graph');
                graphData = await response.json();
                
                if (graphData.nodes && graphData.nodes.length > 0) {
                    renderGraph(graphData);
                } else {
                    document.getElementById('knowledge-graph').innerHTML = '<p style="text-align: center; padding: 50px;">No graph data available</p>';
                }
            } catch (error) {
                console.error('Error loading graph:', error);
            }
        }
        
        function renderGraph(data) {
            const container = document.getElementById('knowledge-graph');
            
            // Convert data to vis.js format
            const nodes = new vis.DataSet(data.nodes.map(node => ({
                id: node.id,
                label: node.label,
                color: node.color,
                size: node.size,
                title: `Type: ${node.type}\\nConcepts: ${node.concepts?.join(', ') || 'None'}`
            })));
            
            const edges = new vis.DataSet(data.edges.map(edge => ({
                from: edge.source,
                to: edge.target,
                label: edge.relationship
            })));
            
            const networkData = { nodes: nodes, edges: edges };
            
            const options = {
                nodes: {
                    font: { size: 12 },
                    borderWidth: 2,
                    shadow: true
                },
                edges: {
                    font: { size: 10 },
                    arrows: { to: { enabled: true } },
                    smooth: { enabled: true }
                },
                physics: {
                    enabled: true,
                    stabilization: { iterations: 100 }
                },
                interaction: {
                    hover: true,
                    selectConnectedEdges: false
                }
            };
            
            new vis.Network(container, networkData, options);
        }
        
        async function loadThemes() {
            try {
                const response = await fetch('/api/themes');
                const data = await response.json();
                
                if (data.labels && data.labels.length > 0) {
                    const plotData = [{
                        type: 'pie',
                        labels: data.labels,
                        values: data.values,
                        textinfo: 'label+percent',
                        textposition: 'outside'
                    }];
                    
                    const layout = {
                        title: data.title,
                        height: 400
                    };
                    
                    Plotly.newPlot('themes-chart', plotData, layout);
                } else {
                    document.getElementById('themes-chart').innerHTML = '<p>No themes available</p>';
                }
            } catch (error) {
                console.error('Error loading themes:', error);
            }
        }
        
        async function loadInsights() {
            try {
                const response = await fetch('/api/insights');
                const data = await response.json();
                
                if (data.insights && data.insights.length > 0) {
                    const insightsHtml = data.insights.map(insight => `
                        <div class="insight-item">
                            <strong>${insight.statement || 'Insight'}</strong>
                            <br><small>Confidence: ${insight.confidence || 'Medium'}</small>
                        </div>
                    `).join('');
                    
                    document.getElementById('insights-container').innerHTML = insightsHtml;
                } else {
                    document.getElementById('insights-container').innerHTML = '<p>No insights available. Build knowledge graph first.</p>';
                }
            } catch (error) {
                console.error('Error loading insights:', error);
                document.getElementById('insights-container').innerHTML = '<p>Error loading insights</p>';
            }
        }
        
        async function performSearch() {
            const query = document.getElementById('search-query').value.trim();
            if (!query) return;
            
            const resultsDiv = document.getElementById('search-results');
            resultsDiv.innerHTML = '<div class="loading">Searching...</div>';
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                });
                
                const data = await response.json();
                
                if (data.results && data.results.length > 0) {
                    const resultsHtml = data.results.map((result, index) => `
                        <div style="margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                            <strong>${index + 1}. ${result.title}</strong>
                            <br><small>Similarity: ${(result.similarity_score * 100).toFixed(1)}%</small>
                        </div>
                    `).join('');
                    
                    resultsDiv.innerHTML = resultsHtml;
                } else {
                    resultsDiv.innerHTML = '<p>No results found</p>';
                }
            } catch (error) {
                console.error('Search error:', error);
                resultsDiv.innerHTML = '<p>Search failed</p>';
            }
        }
        
        // Enable search on Enter key
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('search-query').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    performSearch();
                }
            });
            
            // Load dashboard
            loadDashboard();
        });
        
        // Auto-refresh every 30 seconds
        setInterval(loadStats, 30000);
    </script>
</body>
</html>
'''
    
    def start(self, open_browser: bool = True):
        """Start the dashboard server"""
        
        if self.is_running:
            logger.warning("Dashboard is already running")
            return
        
        def run_server():
            self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.is_running = True
        
        dashboard_url = f"http://{self.host}:{self.port}"
        logger.info(f"AKAP Dashboard started at {dashboard_url}")
        
        if open_browser:
            # Small delay to ensure server is ready
            threading.Timer(1.0, lambda: webbrowser.open(dashboard_url)).start()
        
        return dashboard_url
    
    def stop(self):
        """Stop the dashboard server"""
        # Flask doesn't have a clean way to stop from code
        # In production, would use a proper WSGI server
        self.is_running = False
        logger.info("Dashboard stop requested")
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard usage statistics"""
        return {
            "dashboard_running": self.is_running,
            "host": self.host,
            "port": self.port,
            "url": f"http://{self.host}:{self.port}" if self.is_running else None
        }