<template>
    <div class="chat " :class="sender ? `chat-end` : `chat-start`" :id="hash">
        <div class="chat-header" v-if="first">
            {{ sender ? `` : user }}
            <time class="text-xs opacity-50">{{ timestamp }}</time>
        </div>
        <div class="chat-bubble " :class="sender ? `chat-bubble-info`: `chat-bubble-accent`">{{ message }}</div>
        <div class="chat-footer opacity-50" v-if="last && sender">{{ status ? `Delivered` : `Sending...`}}</div>
    </div>
</template>

<script setup>
import { onMounted } from 'vue'

const props = defineProps({
  user: String,
  // Multiple possible types
  sender: {
    type: Boolean,
    default: true
  },
  timestamp: {
    type: String,
    default: new Date().toLocaleString()
  },
  message: {
    type: String,
    default: ""
  },
  status: {
    type: Boolean,
    default: false
  },
  first: {
    type: Boolean,
    default: true
  },
  last: {
    type: Boolean,
    default: true
  },
  hash: {
    type: String
  }
})

onMounted(() => {
  const message = document.getElementById(props.hash);
  message.scrollIntoView({ behavior: 'smooth' });
})

</script>