<template>
  <div class="container">
    <!-- Header: Participant name, mode toggle and export button -->
    <div class="header">
      <div class="field">
        <label for="name">Name:</label>
        <input id="name" v-model="participantName" type="text" placeholder="Enter your name" />
      </div>
      <div class="field mode-toggle">
        <label>Mode:</label>
        <label> <input type="radio" value="AI" v-model="mode" /> AI </label>
        <label> <input type="radio" value="traditional" v-model="mode" /> Traditional </label>
      </div>
      <label> <input type="checkbox" v-model="developmentBackground" /> Entwickler*in </label>

      <div class="field">
        <button @click="exportJSON">Export</button>
      </div>
    </div>

    <!-- Questionnaire -->
    <div class="questionnaire">
      <div v-for="(qData, index) in questionnaire" :key="index" class="prompt-section">
        <h2>{{ qData.prompt }}</h2>
        <!-- For each category row -->
        <div class="categories">
          <div v-for="(cat, catIndex) in qData.categories" :key="catIndex" class="category">
            <div class="description-left">
              <span>{{ cat.left }}</span>
            </div>
            <div class="options">
              <!-- 5 radio buttons representing a 1-5 scale -->
              <label v-for="n in 5" :key="n">
                <input type="radio" :name="`prompt-${index}-category-${catIndex}`" :value="n" v-model="cat.reply" />
              </label>
            </div>
            <div class="description-right">
              <span>{{ cat.right }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Feedback Section -->
    <div class="feedback-section">
      <h2>Feedback</h2>
      <textarea v-model="feedback" placeholder="Zusätzlich ist mir noch aufgefallen, dass ..."></textarea>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'

// Participant details
const participantName = ref('')
const mode = ref('AI') // default mode
const feedback = ref('') // Feedback text
const developmentBackground = ref(false)

// Define interfaces for TypeScript type checking
interface Category {
  left: string
  right: string
  reply: number | null
}
interface Prompt {
  prompt: string
  name: string
  categories: Category[]
}

// Sample questionnaire data
const questionnaire = reactive<Prompt[]>([
  {
    prompt: 'Für das Erreichen meiner Ziele empfinde ich das Produkt als',
    name: 'Effizienz',
    categories: [
      { left: 'langsam', right: 'schnell', reply: null },
      { left: 'ineffizient', right: 'effizient', reply: null },
    ],
  },
  {
    prompt: 'Die Reaktion des Produkts auf meine Eingaben und Befehle empfinde ich als',
    name: 'Steuerbarkeit',
    categories: [
      { left: 'unberechenbar', right: 'vorhersagbar', reply: null },
      { left: 'behindernd', right: 'unterstützend', reply: null },
    ],
  },
  {
    prompt: 'Die Möglichkeit das Produkt zu nutzen empfinde ich als',
    name: 'Nützlichkeit',
    categories: [
      { left: 'nicht hilfreich', right: 'hilfreich', reply: null },
      { left: 'nicht lohnend', right: 'lohnend', reply: null },
    ],
  },
  {
    prompt: 'Die Bedienung des Produkts wirkt auf mich',
    name: 'Intuitive Bedienung',
    categories: [
      { left: 'mühevoll', right: 'mühelos', reply: null },
      { left: 'unlogisch', right: 'logisch', reply: null },
      { left: 'nicht einleuchtend', right: 'einleuchtend', reply: null },
    ],
  },
  {
    prompt: 'Die Antworten der Suche sind',
    name: 'Antwortqualität',
    categories: [
      { left: 'unpassend', right: 'passend', reply: null },
      { left: 'nicht hilfreich', right: 'hilfreich', reply: null },
      { left: 'unintelligent', right: 'intelligent', reply: null },
      { left: 'schlecht aufbereitet', right: 'gut aufbereitet', reply: null },
      { left: 'ungenau', right: 'genau', reply: null },
    ],
  },
])

// Export function creates a JSON file and triggers a download
function exportJSON() {
  // Build the export object based on the filled questionnaire
  const exportData = {
    name: participantName.value,
    mode: mode.value,
    developer: developmentBackground.value,
    questionnaire: questionnaire.map((q) => ({
      prompt: q.prompt,
      name: q.name,
      categories: q.categories.map((cat) => ({
        left: cat.left,
        right: cat.right,
        reply: cat.reply,
      })),
    })),
    feedback: feedback.value, // Ensure feedback is included
  }

  const jsonString = JSON.stringify(exportData, null)
  console.log(jsonString)
  const blob = new Blob([jsonString], { type: 'application/json' })
  // Create a safe file name: e.g., "John_ai.json" or "John_traditional.json"
  const safeName = participantName.value.trim().replace(/\s+/g, '_') || 'participant'
  const fileName = `${safeName}_${mode.value.toLowerCase()}.json`
  // Trigger download
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = fileName
  link.click()
}
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100%;
}

.header {
  display: flex;
  gap: 20px;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.field {
  display: flex;
  flex-direction: column;
}

.field input[type='text'] {
  padding: 5px;
  font-size: 16px;
  margin-top: 5px;
}

.mode-toggle {
  flex-direction: row;
  align-items: center;
  gap: 10px;
}

.questionnaire {
  margin-top: 20px;
}

.prompt-section {
  margin-bottom: 30px;
  border: 1px solid #ccc;
  padding: 15px;
  border-radius: 8px;
}

.categories {
  margin-bottom: 15px;
  min-width: 584px;
}

.category {
  display: flex;
  align-items: center;
}

.description-left {
  width: 244px;
  font-weight: bold;
  text-align: right;
  padding-right: 5px;
}

.description-right {
  width: 244px;
  font-weight: bold;
  padding-left: 5px;
}

.options {
  min-width: 120px;
}

.options label {
  margin-right: 5px;
  margin-left: 5px;
}

.questionnaire h2 {
  text-align: center;
  margin-bottom: 10px;
}

.feedback-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  margin-bottom: 20vh;
  border: 1px solid #ccc;
  padding: 15px;
  border-radius: 8px;
}

.feedback-section h2 {
  text-align: center;
  margin-bottom: 10px;
}

.feedback-section textarea {
  width: 25vw;
  height: 150px;
  padding: 10px;
  font-size: 16px;
  border: 1px solid #ccc;
  border-radius: 4px;
  resize: vertical;
  min-height: 20vh;
}
</style>
