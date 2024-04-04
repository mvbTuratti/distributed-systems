<template>
  <div class="flex flex-col h-screen">
    <div v-if="!connected" class="h-20 flex justify-center">
      <div role="alert" class="alert alert-error w-[80%] mt-4">
        <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        <span>Error! Lost connection to server</span>
      </div>
    </div>
    <div id="chat" class="flex-1 px-12 mb-8 scrollable-content p-4 overflow-y-auto">
      <template v-for="chat in chats">
        <Message v-bind="chat"></Message>
      </template>
    </div>
    <div id="input_text" class="h-16 flex justify-center p-2">
      <input type="text" placeholder="" @keyup.enter="onEnter" maxlength="4000" v-model="message" class="input input-bordered w-full mx-8" :class="connected ? ``: ` input-disabled`" />
    </div>
    <div class="h-8">
      <span class="text-xs opacity-50 text-white">{{ clientName }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Message from './components/Message.vue'
const message = ref('');
const chats = ref([]);
const selfHashes = new Set();
let socket = null;
const connected = ref(false);
const timeOut = ref(1000);
const clientName = ref("");
const pastNames = new Set();

function checkPosition(user) {
  if (chats.value.length) {
    const lastItem = chats.value[chats.value.length - 1];
    if (lastItem.user === user){
      chats.value[chats.value.length - 1].last = false
      return false
    }
    return true
  }
  return true
}
function onEnter(params) {
  if (connected.value){
    let hash = generateRandomValue();
    chats.value.push({
      user: "", sender: true, hash: hash, message: message.value, 
      last: true, first: checkPosition(""), status: false})
    socket.send(`${hash} - ${message.value}`)
    selfHashes.add(hash);
    message.value = "";
  }
}
function generateRandomValue() {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let randomValue = '';
    for (let i = 0; i < 16; i++) {
        const randomIndex = Math.floor(Math.random() * characters.length);
        randomValue += characters.charAt(randomIndex);
    }
    return randomValue;
}
function handleMessages(event) {
  try {
    let message = JSON.parse(event.data);
    if (!selfHashes.has(message.hash) && !pastNames.has(message.name)){
      chats.value.push({
        user: message.name, hash: message.hash, 
        sender: false, message: message.content, last: true, 
        first: checkPosition(message.name), timestamp: message.timestamp
      })
    } else {
      for (let index = 0; index < chats.value.length; index++) {
        const element = chats.value[index];
        if (element.hash === message.hash){
          chats.value[index].status = true;
        }
      }
    }
  } catch (error) {
    pastNames.add(event.data);
    clientName.value = event.data
  }
}

function failureHandler() {
  connected.value = false;
  if (!connected.value){
    setTimeout(createSocket, timeOut.value);
    timeOut.value = Math.ceil(timeOut.value + 2000, 10000);
  }
}

onMounted(() => {
  fetch(import.meta.env.VITE_API_URL).then(m => m.json()).then(results => {
    for (let index = 0; index < results.messages.length; index++) {
      handleMessages({data: results.messages[index]});
    }
  })
  createSocket();
})

function createSocket() {
  socket = new WebSocket(import.meta.env.VITE_WS_URL)
  socket.onopen = () => { connected.value = true }
  socket.onmessage = (event) => { handleMessages(event) }
  socket.onclose = (e) => {failureHandler()};
  socket.onerror = (e) => {failureHandler()};
}

</script>