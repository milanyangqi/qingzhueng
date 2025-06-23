<script setup lang="ts">
import Dialog from "@/components/dialog/Dialog.vue"

const emit = defineEmits([
  'close',
])

</script>

<template>
  <Dialog
      @close="emit('close')"
      title="反馈">
    <div class="feedback-modal">
      <div>
        给我发Email：<a href="mailto:mail@636m.com">mail@636m.com</a>
      </div>
    </div>
  </Dialog>
</template>

<style scoped lang="scss">
@import "@/assets/css/variable";

.feedback-modal {
  width: 500rem;
  //height: 80vh;
  display: flex;
  flex-direction: column;
  background: var(--color-second-bg);
  align-items: center;
  padding: var(--space);
  //justify-content: center;
  color: var(--color-font-1);


}

</style>