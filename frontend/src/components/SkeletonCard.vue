<template>
  <div class="sk surface" aria-hidden="true">
    <span class="skeleton thumb" />
    <span class="lines">
      <span class="skeleton l1" />
      <span class="skeleton l2" />
      <span class="skeleton l3" />
    </span>
    <span class="skeleton ring" />
    <span class="skeleton bar" />
  </div>
</template>

<style scoped>
.sk {
  display: grid;
  grid-template-columns: 80px 1fr 58px;
  grid-template-areas:
    "thumb lines ring"
    "bar bar bar";
  align-items: center;
  gap: 0.85rem;
  padding: 12px 14px 14px 12px;
}

.thumb {
  grid-area: thumb;
  height: 80px;
  border-radius: var(--r-md);
}

.lines {
  grid-area: lines;
  display: grid;
  gap: 8px;
}

.l1 {
  width: 40%;
  height: 10px;
}

.l2 {
  width: 75%;
  height: 16px;
}

.l3 {
  width: 55%;
  height: 22px;
  border-radius: 999px;
}

.ring {
  grid-area: ring;
  width: 58px;
  height: 58px;
  border-radius: 50%;
}

.bar {
  grid-area: bar;
  height: 26px;
}
</style>
