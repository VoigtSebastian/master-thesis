<template>
  <div class="app-container">
    <!-- State 1: Search Input -->
    <div v-if="currentState === 'search'" class="search-wrapper">
      <h1>Supersuche</h1>
      <div>
        <input autofocus type="text" v-model="query" @keyup.enter="startSearch"
          placeholder="Was bedeutet eigentlich ...?" />
        <div class="tooltip">?
          <span class="tooltiptext">
            <span class="robot-icon">🤖</span>
            <span class="info-text">
              Diese Anwendung ist ein Recherchetool, das dir hilft, Informationen aus verschiedenen Quellen zu sammeln.
              Es erlaubt dir Fragen und Probleme in natürlicher Sprache zu formulieren und reduziert so den Aufwand,
              Informationen zu suchen.
            </span></span>
        </div>
      </div>
    </div>

    <!-- State 2 and 3: Streaming Results and Final Message -->
    <div v-else>
      <div class="query-header">
        <h2>"{{ query }}"</h2>
      </div>
      <!-- Only show results-container if there are results -->
      <div v-if="results.length > 0" class="results-container">
        <div v-for="(result, index) in results" :key="index" class="result-item">
          <div class="result-header" @click="toggle(index)">
            {{ result.event }}
            <span class="arrow-icon" v-if="result.show">^</span>
            <span class="arrow-icon" v-else>v</span>
          </div>
          <!-- Collapsible panel: toggles to show formatted JSON -->
          <div class="result-content" :class="{ 'show-content': result.show }">
            <pre>{{ formatJson(result.data) }}</pre>
          </div>
        </div>
      </div>
      <!-- State 3: Final message rendered as Markdown -->
      <div v-if="finalMessage" class="final-message">
        <div v-html="renderMarkdown(finalMessage)"></div>
        <button class="reset-search" @click="resetSearch">Nächste Suche</button>
      </div>
      <!-- State 4: Error Message -->
      <div v-else-if="errorMessage" class="error-message">
        <p>{{ errorMessage }}</p>
        <button class="reset-search" @click="resetSearch">Reload Page</button>
      </div>
      <div v-else-if="!finalMessage && !errorMessage" class="loader-container">
        <span class="loader"></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { marked } from 'marked'

// Query entered by the user
const query = ref('')
// State to track if the app is in search mode or displaying results
const currentState = ref<'search' | 'results'>('search')
// Array of streamed results (each having an event and a data object)
const results = ref(
  [] as Array<{ event: string; data: any; show: boolean }>
)
// Final message for state 3
const finalMessage = ref('')
// Error message for state 4
const errorMessage = ref('')

// Toggle function for collapsing/expanding each result item
function toggle(index: number) {
  results.value[index].show = !results.value[index].show
}

// Helper to format and indent JSON data
function formatJson(data: any) {
  return JSON.stringify(data, null, 2)
}

// Render markdown to HTML
function renderMarkdown(md: string) {
  return marked(md)
}

// Reset the entire view to start a new query
function resetSearch() {
  query.value = ''
  currentState.value = 'search'
  results.value = []
  finalMessage.value = ''
  errorMessage.value = ''
}

// Start the search and process streaming JSON response
async function startSearch() {
  currentState.value = 'results'
  // Clear previous results if any
  results.value = []
  finalMessage.value = ''
  errorMessage.value = ''

  const url = `http://127.0.0.1:8000/streaming/${encodeURIComponent(query.value)}`

  try {
    const response = await fetch(url)
    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    while (reader) {
      const { value, done } = await reader.read()
      if (done) break

      // Decode the chunk into text and split by lines
      const lines = decoder.decode(value).split('\n')

      for (const line of lines) {
        if (line.trim()) {
          try {
            const payload = JSON.parse(line)
            // Handle "final_message" event separately
            if (payload.event === 'final_message') {
              finalMessage.value = payload.data.message
            } else {
              // Add other events to the collapsible results list
              results.value.push({ event: payload.event, data: payload.data, show: false })
            }
          } catch (e) {
            console.error('Error parsing JSON:', e)
            errorMessage.value = 'A fatal error has occurred. Please reload the page.'
          }
        }
      }
    }
  } catch (error) {
    console.error('Error fetching stream:', error)
    errorMessage.value = 'A fatal error has occurred. Please reload the page.'
  }
}
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100%;
}

.search-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
}

h1 {
  margin-bottom: 20px;
}

input[type="text"] {
  width: 15vw;
  padding: 10px;
}

.query-header {
  text-align: center;
  margin-bottom: 20px;
}

.results-container {
  width: 25vw;
  border: 1px solid #494949;
  padding: 10px;
  border-radius: 5px;
}

.final-message {
  width: 25vw;
  margin-top: 50px;
  margin-bottom: 50px;
}

.result-item {
  border: 1px solid #ccc;
  border-radius: 3px;
  margin: 10px;
  padding: 5px;
}

.result-content {
  overflow: hidden;
  transition: max-height 0.3s ease-out;
  max-height: 0;
}

.result-content.show-content {
  max-height: 20vh;
}

.result-content pre {
  margin: 0;
  padding: 10px;
  white-space: pre-wrap;
  /* Ensure the pre-formatted text wraps */
  word-wrap: break-word;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding: 10px;
  /* border: 1px solid #ccc;
  background-color: #f9f9f9;
  border: 1px solid #ccc;
  border-radius: 3px; */
}

.arrow-icon {
  margin-left: 10px;
  font-weight: bold;
}

.reset-search {
  margin-top: 70px;
  min-width: 5vw;
  min-height: 4vh;
  background-color: orange;
  border-radius: 5px;
  font-weight: bold;
  font-size: large;
}

pre {
  height: auto;
  max-height: 20vh;
  overflow: auto;
  word-break: normal !important;
  word-wrap: normal !important;
  white-space: pre !important;
}

.error-message {
  width: 25vw;
  margin-top: 50px;
  margin-bottom: 50px;
  color: red;
  text-align: center;
}

.error-message p {
  margin-bottom: 20px;
}

.loader-container {
  width: 25vw;
  margin-top: 100px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.loader {
  width: 48px;
  height: 48px;
  border: 5px solid #ff3916;
  border-bottom-color: transparent;
  border-radius: 50%;
  display: inline-block;
  box-sizing: border-box;
  animation: rotation 1s linear infinite;
}

@keyframes rotation {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

/* Tooltip container */
.tooltip {
  position: relative;
  display: inline-block;
  border-bottom: 1px dotted black;
  margin-left: 10px;
  font-weight: bold;
  /* If you want dots under the hoverable text */
}

/* Tooltip text */
.tooltip .tooltiptext {
  visibility: hidden;
  width: 270px;
  background-color: black;
  color: #fff;
  text-align: center;
  padding: 3px;
  border-radius: 6px;

  /* Position the tooltip text - see examples below! */
  position: absolute;
  z-index: 1;
}

/* Show the tooltip text when you mouse over the tooltip container */
.tooltip:hover .tooltiptext {
  visibility: visible;
}

.info-field {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  /* Adjust spacing as needed */
}

.robot-icon {
  font-size: 24px;
  /* Adjust size of the icon */
  margin-right: 10px;
}

.info-text {
  width: 20vw;
  white-space: no-wrap;
  font-size: 14px;
  color: #f0f0f0;
}
</style>
