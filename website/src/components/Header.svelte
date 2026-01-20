<script lang="ts">
	export let link: string;

	let all_tabs = [
		{ name: 'Home', link: '/' },
		{ name: 'Login', link: '/login' },
		{ name: 'Ausprobieren', link: '/try' },
		{ name: 'Kontakt', link: '/contact' },
		{ name: 'About me', link: '/about' }
	];

	let tabs = all_tabs.filter((tab) => tab.link !== link);
</script>

<header
	class="sticky top-0 z-10 flex items-center justify-between border-transparent
  bg-linear-to-b from-fuchsia-900 to-transparent px-6 py-4 backdrop-blur-2xl duration-200"
>
	<h1 class="ton-medium">
		<b style="font-family: 'Montserrat'" class="text-font-bold text-3xl dark:text-white">MHBAI</b>
		<b class="text-xs dark:text-fuchsia-700"> by Leon Gattermeyer</b>
	</h1>
	<div class="hidden items-center gap-4 sm:flex">
		{#each tabs as tab}
			<a
				href={tab.link}
				class="btn btn-outline btn-primary btn-md rounded-full border-3 border-fuchsia-500
        bg-fuchsia-900/20 px-4 py-1 inset-shadow-sm inset-shadow-fuchsia-950 hover:bg-fuchsia-900/40
        hover:inset-shadow-fuchsia-400
        dark:text-white dark:inset-shadow-fuchsia-300
        dark:hover:bg-fuchsia-900/60 dark:hover:inset-shadow-fuchsia-600"
			>
				<p>{tab.name}</p>
			</a>
		{/each}
	</div>
</header>
