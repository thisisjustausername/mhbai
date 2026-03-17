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
    shadow-[_10px_20px_40px_rgba(50,0,50,0.3),inset_0_0_10px_rgba(230,40,180,0.5)] inset-shadow-sm dark:shadow-[inset_0_0_10px_rgba(230,40,180,0.5)]
    focus:bg-fuchsia-300/40 focus:bg-fuchsia-300/60 focus:shadow-[_10px_20px_40px_rgba(50,0,50,0.3),inset_0_0_10px_rgba(25,0,25,0.5)] focus:ring-0
    focus:outline-none dark:bg-fuchsia-500/20 dark:focus:bg-fuchsia-400/30 dark:focus:shadow-[inset_0_0_10px_rgba(25,0,25,0.5)]"
		placeholder="Modulsuche"
	/>
</form>

{#if modules === null}
	<div class="mx-auto mt-30 max-w-3xl rounded-2xl dark:bg-gradient-tobr dark:from-black dark:to-black bg-gradient-to-br from-fuchsia-700 to-cyan-400 p-[2px] dark:p-[0px] shadow-[_10px_20px_40px_rgba(50,0,50,0.3)]
	  dark:border-purple-400 dark:bg-purple-600/30 dark:shadow-[inset_0_0_20px_#9333ea]">
		<div
			class="rounded-2xl dark:border-3 dark:border-fuchsia-800 
			bg-white/70 p-6 dark:shadow-inset[_0_0_40px_rgba(250,100,250,0.7)]
			dark:border-fuchsia-500 dark:bg-fuchsia-400 dark:bg-fuchsia-600/30 
			dark:shadow-[inset_0_0_20px_rgba(255,0,255,0.7)]"
		>
			<h2 class="mb-4 text-2xl font-bold dark:text-gray-200 text-center">Modulsuche erklärt</h2>

			<ul class="list-disc dark:text-gray-200 pl-5">
					<li class="mb-2">Modulcode: Geben Sie den Modulcode ein; um spezifische Module zu finden.
					<!-- <br /><span class="italic">TIPP: Um alle Module einer Fakultät zu finden; suchen Sie nach dem Fakultätskürzel und fügen Sie ein Minuszeichen an (Bsp. Informatik: Inf-)</span></li> -->
					<li>Titel: Geben Sie einen Teil des Modultitels ein; um Module zu finden.</li>
				</ul>
		</div>
		 </div>
{/if}

{#each modules as module}
	<div class="px-3">
		<Module {module} />
	</div>
{/each}


</main>