<template>
  <svg class="brand" viewBox="0 0 40 40" aria-hidden="true">
    <defs>
      <linearGradient id="brand-sweep" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="var(--gold)" stop-opacity="0" />
        <stop offset="1" stop-color="var(--gold)" stop-opacity="0.9" />
      </linearGradient>
    </defs>
    <rect width="40" height="40" rx="12" class="brand-bg" />
    <circle cx="20" cy="20" r="13" class="brand-ring" />
    <circle cx="20" cy="20" r="7.5" class="brand-ring strong" />
    <g class="brand-sweep">
      <path d="M20 20 L20 6 A14 14 0 0 1 32.1 13 Z" fill="url(#brand-sweep)" />
    </g>
    <circle cx="20" cy="20" r="3" class="brand-core" />
  </svg>
</template>

<style scoped>
.brand {
  width: 36px;
  height: 36px;
  flex: none;
}

.brand-bg {
  fill: var(--surface-2);
  stroke: var(--line-2);
}

.brand-ring {
  fill: none;
  stroke: var(--green);
  stroke-width: 1.4;
  opacity: 0.45;
}

.brand-ring.strong {
  stroke: var(--gold);
  opacity: 0.9;
}

.brand-sweep {
  transform-origin: 20px 20px;
  animation: spin 3.2s linear infinite;
}

.brand-core {
  fill: var(--red);
}
</style>
