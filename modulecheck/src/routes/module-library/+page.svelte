<script lang="ts">
	import Module from './components/Module.svelte';

	let modules = $state(null);


	import Header from '../../components/Header.svelte';
	let mods: string = '';
	async function searchModule() {
		const response = await fetch('/api/get-modules', {
			method: 'POST',
			headers: {
				'Content-Type': 'text/plain'
			},
			body: mods
		});
		if (!response.ok) {
			module = null;
			return;
		}
		const data = await response.json();
		modules = data;
	}

</script>

<Header link="/module-library" />

<main class="px-9">

<form class="mt-5 mb-12 flex flex-wrap justify-center" on:submit|preventDefault={searchModule}>
	<input
		bind:value={mods}
		class="w-[50rem] rounded-full border-3 border-fuchsia-500 bg-fuchsia-200/70 py-6 text-center text-lg
    shadow-[inset_0_0_10px_rgba(230,40,180,0.5)] inset-shadow-sm
    focus:bg-fuchsia-300/40 focus:bg-fuchsia-300/60 focus:shadow-[inset_0_0_10px_rgba(25,0,25,0.5)] focus:ring-0
    focus:outline-none dark:bg-fuchsia-500/20 dark:focus:bg-fuchsia-400/30"
		placeholder="Modulsuche"
	/>
</form>

{#each modules as module}
	<div class="flex flex-col items-center">
		<Module {module} />
	</div>
{/each}


</main>