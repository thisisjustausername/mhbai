<script lang="ts">

	const { link } = $props();

	let all_tabs = [
		{ name: 'Home', link: '/' },
		{ name: 'Login', link: '/login' },
		{ name: 'Ausprobieren', link: '/try' },
		{ name: 'Modulbibliothek', link: '/module-library' },
		{ name: 'Kontakt', link: '/contact' },
		{ name: 'About me', link: '/about' }
	];

	let tabs = all_tabs.filter((tab) => tab.link !== link);
</script>
<div class="top-0 fixed w-full">
<div class="bg-gray-200 dark:bg-zinc-900 py-4"></div>
<header
	class="shadow-[0_5px_20px_rgba(0,0,0,0.4),inset_0_0_25px_rgba(120,60,120,0.5)] bg-[linear-gradient(to_bottom,rgba(255,255,255,1.0)_10%,rgba(220,200,220,0.4)_80%)]
	flex items-center justify-between px-6 py-8 rounded-3xl mx-4 backdrop-blur-md

	dark:shadow-[0_5px_20px_rgba(240,200,240,0.4),inset_0_0_70px_rgba(120,80,120,0.8)] dark:border-1 dark:border-fuchsia-400
	dark:bg-[linear-gradient(to_bottom,rgba(20,0,20,1.0)_10%,rgba(50,10,50,0.4)_80%)]"
>
	<h1 class="ton-medium">
		<b
			class="inline-block 
		[background-image:linear-gradient(to_bottom,rgba(230,40,180,0.0)_50%,rgba(200,40,230,1.0)_100%),_linear-gradient(to_right,rgb(230_40_180)_40%,rgb(4_180_186)_85%)]
    bg-clip-text font-montserrat text-3xl font-semibold text-transparent
    dark:bg-[linear-gradient(to_right,rgb(173_0_124)_46%,rgb(4_230_236)_80%,rgb(180_244_246)_100%)]"
			>moduleCheck</b
		>
		<b class="text-xs dark:text-fuchsia-700"> by Leon Gattermeyer</b>
	</h1>

	<div class="hidden items-center gap-4 sm:flex">
		{#each tabs as tab}
				<div class="relative inline-block p-[3px] rounded-full
				bg-gradient-to-br from-cyan-400 to-fuchsia-500">
					<a
						class="block rounded-full bg-[rgb(230,215,230)] px-4 py-1 dark:text-gray-100 
						inset-shadow-sm inset-shadow-fuchsia-950 hover:inset-shadow-fuchsia-100/50
						hover:bg-fuchsia-900/35
						transition duration-200 shadow-lg backdrop-blur-md
						dark:bg-[rgb(90,75,90)]"
						href={tab.link}
					>
						<p>{tab.name}</p>
					</a>
				</div>
		{/each}
	</div>
</header>
</div>
<div class="mb-50"></div>