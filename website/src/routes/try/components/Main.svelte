<script lang="ts">
	// const apiUrl: str = "";
	// const MAX_SIZE: 30 * 1024 * 1024
	// let mhb1?: File;
	// let mhb2?: File;
	// let action_mode?: 'COMPARE' | 'INFORM';
	import CollapseItem from '../../../components/CollapseItem.svelte';

	let progress: number = 0;

	function compareModules(mhb1: string, mhb2: string) {
		// Logik zum Vergleichen der Module
		console.log(`Vergleiche Module: ${mhb1} und ${mhb2}`);
	}
</script>

<!--IMPORTANT SAVE FILES USER INPUT TO USE AS TRAINING DATA!!!-->
<div class="grid grid-cols-[100px_repeat(2,minmax(0,1fr))] gap-0 overflow-x-hidden">
	<!-- Header showing categories and MHB names -->
	<div class="contents">
		<div
			class="min-w-0 border-2 border-gray-800 bg-gray-800 p-2 text-center font-semibold text-rose-600 dark:text-fuchsia-400"
		>
			Kategorien
		</div>
		<div
			class="min-w-0 bg-gray-800 p-2 text-center font-semibold text-rose-600 dark:text-fuchsia-400"
		>
			MHB-Name-1
		</div>
		<div
			class="min-w-0 bg-gray-800 p-2 text-center font-semibold text-rose-600 dark:text-fuchsia-400"
		>
			MHB-Name-2
		</div>
	</div>
	<!-- categories with values -->

	<!-- category 1 -->
	<div class="contents">
		<div
			class="min-w-0 border-2 border-gray-800 bg-gray-800 p-2 text-center font-semibold text-rose-600 dark:text-fuchsia-400"
		>
			Titel
		</div>
		<div
			class="min-w-0 border-2 border-gray-700 bg-gray-800 p-2 text-center text-sm dark:text-white"
		>
			Test Titel
		</div>
		<div
			class="min-w-0 border-2 border-gray-700 bg-gray-800 p-2 text-center text-sm dark:text-white"
		>
			Test Titel
		</div>
	</div>

	<!-- category 2 -->
	<div class="contents">
		<div
			class="min-w-0 border-2 border-gray-800 bg-gray-800 p-2 text-center font-semibold text-rose-600 dark:text-fuchsia-400"
		>
			ECTS
		</div>
		<div
			class="min-w-0 border-2 border-gray-700 bg-gray-800 p-2 text-center text-sm dark:text-white"
		>
			5
		</div>
		<div
			class="min-w-0 border-2 border-gray-700 bg-gray-800 p-2 text-center text-sm dark:text-white"
		>
			0
		</div>
	</div>

	<!-- category 3 -->
	<div class="contents">
		<div
			class="min-w-0 border-2 border-gray-800 bg-gray-800 p-2 text-center font-semibold text-rose-600 dark:text-fuchsia-400"
		>
			Inhalt
		</div>
		<div
			class="wrap-break-words min-w-0 border-2 border-gray-700 bg-gray-800 p-2 text-center
      text-sm dark:text-white"
		>
			asjdkfhasjkdfhajskdfhasj kdfhasjkdfhjkasdhfkjasdhfkjasdfhkjasdhfkjasdhfkjasdhfkjasdf
			hkjasdhfkjasdhfkjasdfhkjasdhfjkashfkasjhfkjsadhfkjsahfjkasdhfkjashfkjashfkjashfkasjhdfkjashfkjashfkjashfkjashfkjasfhkjasfhkasjfhaskjdfhaskjfhkasjdfh
		</div>
		<div
			class="wrap-break-words min-w-0 border-2 border-gray-700 bg-gray-800 p-2 text-center text-sm dark:text-white"
		>
			aklajdfklasjdfk lasjfksajdkflasjfasjfklasjf lajsfklajsfajwflkajsfklasjf
			lkaesjfioawejfoiajflkasejfknjfkasjdfilaksevjiasnajfkasjnckalsjncfiaxsjfcniasjksnoicljaesnonvkcfoilkasjnvdokl
		</div>
	</div>
</div>
<details
	class="group grid grid-cols-1 gap-3 border-2 border-gray-800 text-center
  sm:grid-cols-3 dark:text-white"
>
	<!-- First column (toggler) -->
	<summary
		class="cursor-pointer items-center gap-2 rounded border border-slate-800 px-2 py-1 text-sm select-none hover:bg-fuchsia-500/10"
	>
		<span>Toggle details</span>
		<svg
			class="h-4 w-4 transition-transform group-open:rotate-180"
			viewBox="0 0 20 20"
			fill="currentColor"
			aria-hidden="true"
		>
			<path
				d="M5.23 7.21a.75.75 0 0 1 1.06.02L10 10.94l3.71-3.71a.75.75 0 1 1 1.06 1.06l-4.24 4.24a.75.75 0 0 1-1.06 0L5.21 8.29a.75.75 0 0 1 .02-1.08z"
			/>
		</svg>
	</summary>

	<!-- Collapsible area spans remaining two columns -->
	<div
		class="max-h-0 overflow-hidden opacity-0 transition-[max-height,opacity] duration-300 group-open:max-h-250 group-open:opacity-100 sm:col-span-2"
	>
		<div class="grid grid-cols-2 gap-3 sm:grid-cols-2">
			<div class="rounded bg-black p-3">Item B</div>
			<div class="rounded bg-slate-100 p-3">Item C</div>
		</div>
	</div>
</details>

<!-- Regular rows -->
<div class="mb-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
	<div class="rounded bg-slate-100 p-3">Row A — Col 1</div>
	<div class="rounded bg-slate-100 p-3">Row A — Col 2</div>
	<div class="rounded bg-slate-100 p-3">Row A — Col 3</div>
</div>

<!-- Special row: first column toggles, other two collapse -->
<details class="group mb-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
	<!-- Col 1: toggler -->
	<summary
		class="inline-flex cursor-pointer items-center gap-2 rounded border border-slate-300 px-2 py-1 text-sm select-none hover:bg-slate-50"
	>
		<span>Toggle row B</span>
		<svg
			class="h-4 w-4 transition-transform group-open:rotate-180"
			viewBox="0 0 20 20"
			fill="currentColor"
			aria-hidden="true"
		>
			<path
				d="M5.23 7.21a.75.75 0 0 1 1.06.02L10 10.94l3.71-3.71a.75.75 0 1 1 1.06 1.06l-4.24 4.24a.75.75 0 0 1-1.06 0L5.21 8.29a.75.75 0 0 1 .02-1.08z"
			/>
		</svg>
	</summary>

	<!-- Cols 2–3: collapse together -->
	<div
		class="max-h-0 overflow-hidden opacity-0 transition-[max-height,opacity] duration-300 group-open:max-h-250 group-open:opacity-100 sm:col-span-2"
	>
		<div class="grid-span grid gap-3 sm:grid-cols-2">
			<div class="rounded bg-slate-100 p-3">Row B — Col 2</div>
			<div class="rounded bg-slate-100 p-3">Row B — Col 3</div>
		</div>
	</div>
</details>

<!-- More rows -->
<div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
	<div class="rounded bg-slate-100 p-3">Row C — Col 1</div>
	<div class="rounded bg-slate-100 p-3">Row C — Col 2</div>
	<div class="rounded bg-slate-100 p-3">Row C — Col 3</div>
</div>
