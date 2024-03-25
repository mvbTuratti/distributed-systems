<template>
    <div class="chat " :class="sender ? `chat-end` : `chat-start`">
        <div class="chat-header">
            {{ user }}
            <time class="text-xs opacity-50">{{ timestamp }}</time>
        </div>
        <div class="chat-bubble " :class="sender ? `chat-bubble-info`: `chat-bubble-accent`">{{ message }}</div>
        <div class="chat-footer opacity-50">{{ status }}</div>
    </div>
</template>

<script setup>
const props = defineProps({
  user: String,
  // Multiple possible types
  sender: {
    type: Boolean,
    default: true
  },
  timestamp: {
    type: String,
    default: "just now"
  },
  message: {
    type: String,
    default: ""
  },
  status: {
    type: String,
    default: "Delivered"
  }
})

</script>