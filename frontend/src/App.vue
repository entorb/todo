<script setup lang="ts">
// Authentication state is restored by the router guard
</script>

<template>
  <q-layout view="hHh lpR fFf">
    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<style>
:root {
  --column-bg: #eceff1;
  --card-bg: #fff;
  --card-done-bg: #f5f5f5;
  --card-fg: #222;
  --add-card-bg: rgb(255 255 255 / 50%);
  --ghost-bg: #cfd8dc;
  --selected-outline: #1976d2;
}
body.body--dark {
  --column-bg: #263238;
  --card-bg: #37474f;
  --card-done-bg: #2e3b42;
  --card-fg: #eceff1;
  --add-card-bg: rgb(255 255 255 / 8%);
  --ghost-bg: #455a64;
  --selected-outline: #64b5f6;
}
body {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) fixed;
  min-height: 100vh;
}
</style>
