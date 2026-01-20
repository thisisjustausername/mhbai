<script lang="ts">
	import { onMount } from 'svelte';
	import { afterNavigate } from '$app/navigation';
	import './layout.css';
	import favicon from '$lib/assets/favicon.ico';

	let { children } = $props();

	let dark_mode: boolean = true;

	// Toggle dark_mode in order to turn dark mode on/off
	function toggleDarkMode(dark?: boolean) {
		dark_mode = dark === undefined ? !dark_mode : dark;
		document.documentElement.classList.toggle('dark', dark_mode);
		try {
			localStorage.theme = dark_mode ? 'dark' : 'light';
		} catch (e) {}
	}
	onMount(() => {
		dark_mode = localStorage.theme === 'dark';
		toggleDarkMode(dark_mode);
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<meta charset="UTF-8" />
	<meta name="viewport" content="width=device-width, initial-scale=1.0" />
</svelte:head>
<div class="full">
	{@render children()}
</div>
