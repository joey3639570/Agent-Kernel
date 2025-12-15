/**
 * Pinia store for managing the Node Editor state.
 * Handles agents, relationships, and config generation.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useNodeEditorStore = defineStore('nodeEditor', () => {
  // State
  const nodes = ref([])
  const edges = ref([])
  const selectedNode = ref(null)
  const selectedEdge = ref(null)
  const isDirty = ref(false)

  // Default agent template
  const defaultAgentProperties = {
    name: 'New Agent',
    role: 'assistant',
    model: 'default',
    personality: {
      openness: 0.5,
      conscientiousness: 0.5,
      extraversion: 0.5,
      agreeableness: 0.5,
      neuroticism: 0.5,
    },
    memory_enabled: true,
    tools_enabled: true,
  }

  // Computed
  const agentNodes = computed(() =>
    nodes.value.filter((n) => n.type === 'agent')
  )

  const relationEdges = computed(() =>
    edges.value.filter((e) => e.type === 'relation')
  )

  const configJson = computed(() => {
    const agents = agentNodes.value.map((node) => ({
      id: node.id,
      name: node.data.name,
      role: node.data.role,
      model: node.data.model,
      personality: node.data.personality,
      memory_enabled: node.data.memory_enabled,
      tools_enabled: node.data.tools_enabled,
    }))

    const relations = relationEdges.value.map((edge) => ({
      source: edge.source,
      target: edge.target,
      relation_type: edge.data?.relation_type || 'neutral',
      weight: edge.data?.weight || 0,
    }))

    return {
      version: '1.0',
      agents,
      relations,
      generated_at: new Date().toISOString(),
    }
  })

  // Actions
  function addAgentNode(position = { x: 100, y: 100 }) {
    const id = `agent_${Date.now()}`
    const newNode = {
      id,
      type: 'agent',
      position,
      data: {
        ...JSON.parse(JSON.stringify(defaultAgentProperties)),
        name: `Agent ${nodes.value.length + 1}`,
      },
    }
    nodes.value.push(newNode)
    isDirty.value = true
    return newNode
  }

  function updateNodeData(nodeId, data) {
    const node = nodes.value.find((n) => n.id === nodeId)
    if (node) {
      node.data = { ...node.data, ...data }
      isDirty.value = true
    }
  }

  function removeNode(nodeId) {
    const index = nodes.value.findIndex((n) => n.id === nodeId)
    if (index !== -1) {
      nodes.value.splice(index, 1)
      // Remove connected edges
      edges.value = edges.value.filter(
        (e) => e.source !== nodeId && e.target !== nodeId
      )
      isDirty.value = true
    }
  }

  function addRelationEdge(source, target, data = {}) {
    const id = `edge_${Date.now()}`
    const newEdge = {
      id,
      type: 'relation',
      source,
      target,
      data: {
        relation_type: data.relation_type || 'neutral',
        weight: data.weight || 0,
        ...data,
      },
    }
    edges.value.push(newEdge)
    isDirty.value = true
    return newEdge
  }

  function updateEdgeData(edgeId, data) {
    const edge = edges.value.find((e) => e.id === edgeId)
    if (edge) {
      edge.data = { ...edge.data, ...data }
      isDirty.value = true
    }
  }

  function removeEdge(edgeId) {
    const index = edges.value.findIndex((e) => e.id === edgeId)
    if (index !== -1) {
      edges.value.splice(index, 1)
      isDirty.value = true
    }
  }

  function selectNode(nodeId) {
    selectedNode.value = nodes.value.find((n) => n.id === nodeId) || null
    selectedEdge.value = null
  }

  function selectEdge(edgeId) {
    selectedEdge.value = edges.value.find((e) => e.id === edgeId) || null
    selectedNode.value = null
  }

  function clearSelection() {
    selectedNode.value = null
    selectedEdge.value = null
  }

  function clearAll() {
    nodes.value = []
    edges.value = []
    selectedNode.value = null
    selectedEdge.value = null
    isDirty.value = false
  }

  function loadFromConfig(config) {
    clearAll()

    // Load agents as nodes
    if (config.agents) {
      config.agents.forEach((agent, index) => {
        const node = {
          id: agent.id || `agent_${index}`,
          type: 'agent',
          position: { x: 150 + (index % 4) * 300, y: 100 + Math.floor(index / 4) * 250 },
          data: {
            name: agent.name || `Agent ${index + 1}`,
            role: agent.role || 'assistant',
            model: agent.model || 'default',
            personality: agent.personality || defaultAgentProperties.personality,
            memory_enabled: agent.memory_enabled !== false,
            tools_enabled: agent.tools_enabled !== false,
          },
        }
        nodes.value.push(node)
      })
    }

    // Load relations as edges
    if (config.relations) {
      config.relations.forEach((relation) => {
        const edge = {
          id: `edge_${relation.source}_${relation.target}`,
          type: 'relation',
          source: relation.source,
          target: relation.target,
          data: {
            relation_type: relation.relation_type || 'neutral',
            weight: relation.weight || 0,
          },
        }
        edges.value.push(edge)
      })
    }

    isDirty.value = false
  }

  function exportAsYaml() {
    // Will be implemented with js-yaml
    return configJson.value
  }

  function markClean() {
    isDirty.value = false
  }

  return {
    // State
    nodes,
    edges,
    selectedNode,
    selectedEdge,
    isDirty,

    // Computed
    agentNodes,
    relationEdges,
    configJson,

    // Actions
    addAgentNode,
    updateNodeData,
    removeNode,
    addRelationEdge,
    updateEdgeData,
    removeEdge,
    selectNode,
    selectEdge,
    clearSelection,
    clearAll,
    loadFromConfig,
    exportAsYaml,
    markClean,
  }
})

