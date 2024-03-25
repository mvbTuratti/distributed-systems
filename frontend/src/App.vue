<template>
  <div class="grid grid-rows-5 h-screen ">
    <div id="chat" class="row-span-4 px-12 mb-8 scrollable-content p-4 overflow-y-auto">
      <template v-for="chat in chats">
        <Message v-bind="chat"></Message>
      </template>
    </div>
    <div id="input_text" class="flex justify-center pt-2">
      <input type="text" placeholder="" @keyup.enter="onEnter" v-model="message" class="input input-bordered w-full mx-8" />
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import Message from './components/Message.vue'
const message = ref('');
const chats = ref([]);

function onEnter(params) {
  console.log(message.value);
  chats.value.push({user: "Example", sender: true, message: message.value})
  message.value = "";
}

</script>