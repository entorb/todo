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
body {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) fixed;
  min-height: 100vh;
}
</style>
