"""React Flow wrapper for Reflex - @xyflow/react v12.

Wraps @xyflow/react as Reflex NoSSR components (React Flow requires
client-side rendering). Includes custom process node types injected
via _get_custom_code().
"""

import reflex as rx
from typing import Any


class ReactFlowLib(rx.NoSSRComponent):
    """Base component for @xyflow/react library."""

    library = "@xyflow/react@12.9.0"

    def _get_custom_code(self) -> str:
        return "import '@xyflow/react/dist/style.css';"


class ReactFlowComponent(ReactFlowLib):
    """Main ReactFlow canvas component."""

    tag = "ReactFlow"
    is_default = False

    nodes: rx.Var[list[dict[str, Any]]]
    edges: rx.Var[list[dict[str, Any]]]
    node_types: rx.Var[dict[str, Any]]
    fit_view: rx.Var[bool] = True  # type: ignore
    color_mode: rx.Var[str] = "dark"  # type: ignore
    nodes_draggable: rx.Var[bool] = True  # type: ignore
    nodes_connectable: rx.Var[bool] = False  # type: ignore
    zoom_on_scroll: rx.Var[bool] = True  # type: ignore
    pan_on_drag: rx.Var[bool] = True  # type: ignore
    min_zoom: rx.Var[float] = 0.3  # type: ignore
    max_zoom: rx.Var[float] = 2.0  # type: ignore

    on_nodes_change: rx.EventHandler[lambda e0: [e0]]
    on_node_click: rx.EventHandler[lambda e0, e1: [e1]]

    def _get_custom_code(self) -> str:
        return _REACT_FLOW_CUSTOM_CODE


class Background(ReactFlowLib):
    """React Flow Background sub-component."""

    tag = "Background"
    variant: rx.Var[str] = "dots"  # type: ignore
    gap: rx.Var[int] = 20  # type: ignore
    size: rx.Var[int] = 1  # type: ignore
    color: rx.Var[str] = "#333"  # type: ignore


class Controls(ReactFlowLib):
    """React Flow Controls sub-component."""

    tag = "Controls"
    show_zoom: rx.Var[bool] = True  # type: ignore
    show_fit_view: rx.Var[bool] = True  # type: ignore
    show_interactive: rx.Var[bool] = False  # type: ignore


class MiniMap(ReactFlowLib):
    """React Flow MiniMap sub-component."""

    tag = "MiniMap"
    node_stroke_color: rx.Var[str] = "#555"  # type: ignore
    node_color: rx.Var[str] = "#333"  # type: ignore


class ReactFlowProvider(rx.NoSSRComponent):
    """ReactFlowProvider wrapper - required parent for ReactFlow."""

    library = "@xyflow/react@12.9.0"
    tag = "ReactFlowProvider"


# Convenience constructors
react_flow = ReactFlowComponent.create
react_flow_background = Background.create
react_flow_controls = Controls.create
react_flow_minimap = MiniMap.create
react_flow_provider = ReactFlowProvider.create


# ---------------------------------------------------------------------------
# Custom JS code injected via _get_custom_code()
# Includes: CSS import, custom node types (process nodes with glow effects)
# ---------------------------------------------------------------------------

_REACT_FLOW_CUSTOM_CODE = """
import '@xyflow/react/dist/style.css';
import { Handle, Position } from '@xyflow/react';

const _buildTooltip = (data) => {
  const parts = [data.label];
  if (data.metrics?.count != null) parts.push(`Count: ${data.metrics.count}`);
  if (data.metrics?.avg_duration) parts.push(`Avg duration: ${data.metrics.avg_duration}`);
  if (data.metrics?.is_bottleneck) parts.push('⚠ Bottleneck');
  if (data.icon) parts.push(`Icon: ${data.icon}`);
  return parts.join('\\n');
};

const ProcessTaskNode = ({ data }) => {
  const isBottleneck = data.metrics?.is_bottleneck;
  return (
    <div title={_buildTooltip(data)} style={{
      padding: '12px 20px', borderRadius: '8px',
      border: `2px solid ${data.color || '#6b7280'}`,
      background: `linear-gradient(135deg, ${data.color || '#6b7280'}15, ${data.color || '#6b7280'}08)`,
      color: 'var(--gray-12)', fontSize: '13px', fontWeight: 500,
      textAlign: 'center', minWidth: '140px',
      boxShadow: isBottleneck
        ? `0 0 15px ${data.color}60, 0 0 30px ${data.color}30`
        : `0 0 8px ${data.color || '#6b7280'}20`,
      transition: 'box-shadow 0.3s ease, transform 0.2s ease',
    }}>
      <div>{data.label}</div>
      {data.metrics?.count != null && (
        <div style={{fontSize:'11px', opacity:0.7, marginTop:4}}>
          {data.metrics.count} items
        </div>
      )}
      {data.metrics?.avg_duration && !data.metrics?.is_bottleneck && (
        <div style={{fontSize:'10px', opacity:0.6, marginTop:2}}>
          ~{data.metrics.avg_duration}
        </div>
      )}
      {data.metrics?.is_bottleneck && (
        <div style={{fontSize:'10px', color:'#ef4444', marginTop:2, fontWeight:600}}>
          ⚠ Bottleneck {data.metrics.bottleneck_duration || ''}
        </div>
      )}
      <Handle type="target" position={Position.Top} style={{background: data.color || '#6b7280'}} />
      <Handle type="source" position={Position.Bottom} style={{background: data.color || '#6b7280'}} />
    </div>
  );
};

const ProcessStartNode = ({ data }) => (
  <div title={_buildTooltip(data)} style={{
    padding: '10px 24px', borderRadius: '24px',
    border: `2px solid ${data.color || '#22c55e'}`,
    background: `linear-gradient(135deg, ${data.color || '#22c55e'}15, ${data.color || '#22c55e'}08)`,
    color: 'var(--gray-12)', fontSize: '13px', fontWeight: 600,
    textAlign: 'center', boxShadow: `0 0 12px ${data.color || '#22c55e'}30`,
  }}>
    {data.label}
    {data.metrics?.count != null && (
      <div style={{fontSize:'10px', opacity:0.6, marginTop:2}}>
        {data.metrics.count} items
      </div>
    )}
    <Handle type="source" position={Position.Bottom} style={{background: data.color || '#22c55e'}} />
  </div>
);

const ProcessEndNode = ({ data }) => (
  <div title={_buildTooltip(data)} style={{
    padding: '10px 24px', borderRadius: '24px',
    border: `2px solid ${data.color || '#ef4444'}`,
    background: `linear-gradient(135deg, ${data.color || '#ef4444'}15, ${data.color || '#ef4444'}08)`,
    color: 'var(--gray-12)', fontSize: '13px', fontWeight: 600,
    textAlign: 'center', boxShadow: `0 0 12px ${data.color || '#ef4444'}30`,
  }}>
    {data.label}
    {data.metrics?.count != null && (
      <div style={{fontSize:'10px', opacity:0.6, marginTop:2}}>
        {data.metrics.count} items
      </div>
    )}
    <Handle type="target" position={Position.Top} style={{background: data.color || '#ef4444'}} />
  </div>
);

const ProcessGatewayNode = ({ data }) => (
  <div title={_buildTooltip(data)} style={{
    width: 50, height: 50, transform: 'rotate(45deg)',
    border: `2px solid ${data.color || '#a855f7'}`,
    background: `linear-gradient(135deg, ${data.color || '#a855f7'}15, ${data.color || '#a855f7'}08)`,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    boxShadow: `0 0 12px ${data.color || '#a855f7'}30`,
  }}>
    <div style={{transform:'rotate(-45deg)', color:'#e0e0e0', fontSize:11, textAlign:'center'}}>
      {data.label}
    </div>
    <Handle type="target" position={Position.Top} style={{transform:'rotate(-45deg)', background: data.color || '#a855f7'}} />
    <Handle type="source" position={Position.Bottom} style={{transform:'rotate(-45deg)', background: data.color || '#a855f7'}} />
  </div>
);

const ProcessCurrentNode = ({ data }) => (
  <div title={_buildTooltip(data)} style={{
    padding: '12px 20px', borderRadius: '8px',
    border: `2px dashed ${data.color || '#3b82f6'}`,
    background: `linear-gradient(135deg, ${data.color || '#3b82f6'}20, ${data.color || '#3b82f6'}10)`,
    color: 'var(--gray-12)', fontSize: '13px', fontWeight: 500,
    textAlign: 'center', minWidth: '140px',
    boxShadow: `0 0 12px ${data.color || '#3b82f6'}40, 0 0 24px ${data.color || '#3b82f6'}20`,
  }}>
    <div style={{display:'flex', alignItems:'center', justifyContent:'center', gap:'6px'}}>
      <span className="current-node-dot" style={{
        display:'inline-block', width:8, height:8, borderRadius:'50%',
        background: data.color || '#3b82f6',
      }} />
      {data.label}
    </div>
    {data.metrics?.count != null && (
      <div style={{fontSize:'11px', opacity:0.7, marginTop:4}}>
        {data.metrics.count} items
      </div>
    )}
    {data.metrics?.avg_duration && (
      <div style={{fontSize:'10px', opacity:0.6, marginTop:2}}>
        ~{data.metrics.avg_duration}
      </div>
    )}
    <Handle type="target" position={Position.Top} style={{background: data.color || '#3b82f6'}} />
    <Handle type="source" position={Position.Bottom} style={{background: data.color || '#3b82f6'}} />
  </div>
);

const processNodeTypes = {
  processTask: ProcessTaskNode,
  processStart: ProcessStartNode,
  processEnd: ProcessEndNode,
  processGateway: ProcessGatewayNode,
  processCurrent: ProcessCurrentNode,
};
"""
