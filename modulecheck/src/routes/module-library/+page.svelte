<script lang="ts">
	import Header from '../../components/Header.svelte';
	import Module from './components/Module.svelte';
	import { onMount } from 'svelte';

	let modules = $state(null);
	let filters = $state(null);

	let search = $state();

	onMount(() => {
		loadFilters();
	});

	async function loadFilters() {
		const response = await fetch('/api/get-filter-options');
		if (!response.ok) {
			return;
		}
		filters = await response.json();
	}

	async function search_modules() {
		if (!search) return;
		search.requestSubmit();
	}

	async function handle_submit(event) {
		event.preventDefault();
		const formData = new FormData(search);
		const values = Object.fromEntries(formData.entries());
		const response = await fetch('/api/get-modules', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(values)
		});
		if (!response.ok) {
			modules = null;
			return;
		}
		const data = await response.json();
		modules = data;
		console.log(modules);
	}

</script>

<Header link="/module-library" />

<main class="px-9">
	<div class="mx-auto max-w-8xl mb-30 bg-gradient-to-br from-fuchsia-700 to-cyan-400 p-[3px] dark:p-[0px] shadow-[_10px_20px_40px_rgba(50,0,50,0.3)] dark:from-black dark:to-black dark:shadow-none rounded-2xl">
			<div
			class="rounded-2xl dark:border-3 p-6 grid justify-items-center bg-white/80
			dark:border-cyan-400 dark:shadow-[inset_0_0_40px_#1e40af] dark:bg-blue-800/10"
		>
			<h1 class="text-2xl font-medium mb-5 text-center mt-3">Suche</h1>
			<form class="grid grid-cols-3 gap-x-15" bind:this={search} onsubmit={handle_submit}>

			<!-- Modulcode -->
			<div class="flex gap-x-2 items-center mb-5">
			<span class="text-center">Modulcode:</span>
				<input
					name="module_code"
					type="text"
					placeholder="Modulcode"
					class="w-28 rounded-xl 
					dark:bg-blue-800/30 dark:border-cyan-400 dark:shadow-[inset_0_0_20px_#1e40af] 
					dark:text-white dark:placeholder-gray-400 text-center dark:focus:ring-1 dark:focus:ring-fuchsia-400"
				/>
			</div>

			<!-- ECTS -->
			<div class="flex gap-x-2 items-center mb-5">
			<span class="text-center">ECTS:</span>
				<select name="ects_type" class="dark:text-white rounded-xl dark:bg-blue-800/30 dark:border-cyan-400 dark:shadow-[inset_0_0_20px_#1e40af] w-35">
					<option value="=" selected class="dark:bg-blue-900">exakt</option>
					<option value=">=" class="dark:bg-blue-900">mindestens</option>
					<option value="<=" class="dark:bg-blue-900">höchstens</option>
				</select>
				<input
					name="ects"
					type="number"
					min="0"
					placeholder="ECTS"
					class="w-22 rounded-xl 
					dark:bg-blue-800/30 dark:border-cyan-400 dark:shadow-[inset_0_0_20px_#1e40af] 
					dark:text-white dark:placeholder-gray-400 text-center dark:focus:ring-1 dark:focus:ring-fuchsia-400"
				/>
			</div>


			<!-- title -->
			<div class="flex gap-x-2 items-center mb-5">
			<span class="text-center">Titel:</span>
				<input
					name="title"
					type="text"
					placeholder="Titel"
					class="w-90 rounded-xl 
					dark:bg-blue-800/30 dark:border-cyan-400 dark:shadow-[inset_0_0_20px_#1e40af] 
					dark:text-white dark:placeholder-gray-400 text-center dark:focus:ring-1 dark:focus:ring-fuchsia-400"
				/>
			</div>

			<!-- lecturer -->
			<div class="flex gap-x-2 items-center mb-5">
			<span class="text-center">Dozent*in:</span>
				<input
					name="lecturer"
					type="text"
					placeholder="Dozent*in"
					class="w-65 rounded-xl 
					dark:bg-blue-800/30 dark:border-cyan-400 dark:shadow-[inset_0_0_20px_#1e40af] 
					dark:text-white dark:placeholder-gray-400 text-center dark:focus:ring-1 dark:focus:ring-fuchsia-400"
				/>
			</div>

			<!-- weekly_hours -->
			<div class="flex gap-x-2 items-center mb-5">
			<span class="text-center">SWS:</span>
				<select name="weekly_hours_type" class="dark:text-white rounded-xl dark:bg-blue-800/30 dark:border-cyan-400 dark:shadow-[inset_0_0_20px_#1e40af] w-35">
					<option value="=" selected class="dark:bg-blue-900">exakt</option>
					<option value=">=" class="dark:bg-blue-900">mindestens</option>
					<option value="<=" class="dark:bg-blue-900">höchstens</option>
				</select>
				<input
					name="weekly_hours"
					type="number"
					min="0"
					placeholder="SWS"
					class="w-22 rounded-xl 
					dark:bg-blue-800/30 dark:border-cyan-400 dark:shadow-[inset_0_0_20px_#1e40af] 
					dark:text-white dark:placeholder-gray-400 text-center dark:focus:ring-1 dark:focus:ring-fuchsia-400"
				/>
			</div>

			<!-- recommended_semester -->
			<div class="flex gap-x-2 items-center mb-5">
			<span class="text-center">Empfohlenes Semester:</span>
				<select name="recommended_semester_type" class="dark:text-white rounded-xl dark:bg-blue-800/30 dark:border-cyan-400 dark:shadow-[inset_0_0_20px_#1e40af] w-35">
					<option value="=" selected class="dark:bg-blue-900">exakt</option>
					<option value=">=" class="dark:bg-blue-900">mindestens</option>
					<option value="<=" class="dark:bg-blue-900">höchstens</option>
				</select>
				<input
					name="recommended_semester"
					type="number"
					min="1"
					placeholder="Sem."
					class="w-22 rounded-xl 
					dark:bg-blue-800/30 dark:border-cyan-400 dark:shadow-[inset_0_0_20px_#1e40af] 
					dark:text-white dark:placeholder-gray-400 text-center dark:focus:ring-1 dark:focus:ring-fuchsia-400"
				/>
			</div>

			<!-- version -->
			<div class="flex gap-x-2 items-center mb-5">
			<span class="text-center">MHB-Version:</span>
				<select name="version" class="dark:text-white rounded-xl dark:bg-blue-800/30 dark:border-cyan-400 dark:shadow-[inset_0_0_20px_#1e40af] w-40">
					<option value="" selected class="dark:bg-blue-900">Alle</option>
					{#each filters?.version as version}
						<option value={version} class="dark:bg-blue-900">{version}</option>
					{/each}
				</select>
			</div>

			<!-- Subject -->
			<div class="flex gap-x-2 items-center mb-5">
			<span class="text-center">Fach:</span>
				<select name="subject" class="dark:text-white rounded-xl dark:bg-blue-800/30 dark:border-cyan-400 dark:shadow-[inset_0_0_20px_#1e40af] w-25">
					<option value="" selected class="dark:bg-blue-900">Alle</option>
					{#each filters?.subject as subject}
						<option value={subject} class="dark:bg-blue-900">{subject}</option>
					{/each}
				</select>
			</div>

			</form>
			<div class="p-[2px] rounded-full w-128 mt-7
				bg-gradient-to-br from-cyan-400 to-fuchsia-500">
					<button
						onclick={search_modules}
						class="block rounded-full bg-gray-100 py-2 w-127 dark:text-gray-100 
						shadow-[inset_0_2px_7px_#4a044e] hover:shadow-[inset_0_2px_10px_#6b21a8]
						hover:bg-gray-100/60
						transition duration-200 backdrop-blur-md
						dark:bg-black/50 hover:cursor-pointer dark:text-gray-200 dark:hover:text-black"
						
					>
					<span class="font-semibold text-md ">Suchen</span>
				</button>
				</div>
			
		</div>
</div>


{#if modules === null}
	<div class="mx-auto max-w-3xl rounded-2xl dark:bg-gradient-tobr dark:from-black dark:to-black bg-gradient-to-br from-fuchsia-700 to-cyan-400 p-[2px] dark:p-[0px] shadow-[_10px_20px_40px_rgba(50,0,50,0.3)]
	  dark:border-purple-400 dark:bg-purple-600/30 dark:shadow-[inset_0_0_20px_#9333ea]">
		<div
			class="rounded-2xl dark:border-3 dark:border-fuchsia-800 
			bg-white/70 p-6 dark:shadow-inset[_0_0_40px_rgba(250,100,250,0.7)]
			dark:border-fuchsia-500 dark:bg-fuchsia-400 dark:bg-fuchsia-600/30 
			dark:shadow-[inset_0_0_20px_rgba(255,0,255,0.7)]"
		>
			<h2 class="mb-4 text-2xl font-bold dark:text-gray-200 text-center">Modulsuche erklärt</h2>

			<ul class="list-disc dark:text-gray-200 pl-5">
					<li class="mb-2">Modulcode: Geben Sie den Modulcode ein; um spezifische Module zu finden.</li>
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