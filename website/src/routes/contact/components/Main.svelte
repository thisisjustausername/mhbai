<script lang="ts">
</script>

<section class="">
	<div class="mx-auto max-w-3xl px-4 py-8 lg:py-16">
		<h2
			class="mb-4 text-center text-4xl font-extrabold tracking-tight text-gray-900 dark:text-white"
		>
			Contact Us
		</h2>
		<p class="mb-8 text-center font-light text-gray-500 sm:text-xl lg:mb-16 dark:text-gray-400">
			Sie sind an MHBAI interessiert und wollen es an Ihrer Universität, Hochschule oder Ihrem
			Unternehmen nutzen?<br />Dann treten Sie mit uns in Kontakt.<br />Wir helfen Ihnen bei der
			Einrichtung und stehen Ihnen bei Fragen zur Verfügung.<br />Und das Beste: Das ist ebenso
			<span class="font-bold text-rose-600 dark:text-fuchsia-400">kostenlos</span> wie MHBAI selbst.
		</p>
		<form action="#" class="space-y-8">
			<div>
				<label for="name" class="mb-2 block text-sm font-medium text-gray-900 dark:text-gray-300"
					>Name</label
				>
				<input
					type="text"
					id="name"
					class="focus:ring-primary-500 focus:border-primary-500 dark:focus:ring-primary-500
          dark:focus:border-primary-500 dark:shadow-sm-light block w-full rounded-lg border-2
          border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 shadow-sm dark:border-fuchsia-600
          dark:bg-gray-700 dark:text-white dark:placeholder-gray-400"
					placeholder="Bitte geben Sie Ihren Namen an"
					required
				/>
			</div>
			<div>
				<label for="email" class="mb-2 block text-sm font-medium text-gray-900 dark:text-gray-300"
					>Email-Adresse</label
				>
				<input
					type="email"
					id="email"
					class="focus:ring-primary-500 focus:border-primary-500 dark:focus:ring-primary-500
          dark:focus:border-primary-500 dark:shadow-sm-light block w-full rounded-lg border-2
          border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 shadow-sm dark:border-fuchsia-600
          dark:bg-gray-700 dark:text-white dark:placeholder-gray-400"
					placeholder="Bitte geben Sie Ihre Email-Adresse an"
					required
				/>
			</div>
			<div>
				<label
					for="Einrichtung"
					class="mb-2 block text-sm font-medium text-gray-900 dark:text-gray-300">Einrichtung</label
				>
				<input
					type="text"
					id="subject"
					class="focus:ring-primary-500 focus:border-primary-500 dark:focus:ring-primary-500
          dark:focus:border-primary-500 dark:shadow-sm-light block w-full rounded-lg border-2
          border-gray-300 bg-gray-50 p-3 text-sm text-gray-900 shadow-sm dark:border-fuchsia-600
          dark:bg-gray-700 dark:text-white dark:placeholder-gray-400"
					placeholder="Bitte geben Sie Ihre Einrichtung an"
					required
				/>
			</div>
			<div class="sm:col-span-2">
				<label
					for="information"
					class="mb-2 block text-sm font-medium text-gray-900 dark:text-gray-300"
					>Angabe Ihrer geplanten Nutzung von MHBAI sowie weiterer Informationen</label
				>
				<textarea
					id="message"
					rows="6"
					class="focus:ring-primary-500 focus:border-primary-500 dark:focus:ring-primary-500
          dark:focus:border-primary-500 block w-full rounded-lg border-2 border-gray-300 bg-gray-50
          p-2.5 text-sm text-gray-900 shadow-sm dark:border-fuchsia-600 dark:bg-gray-700
          dark:text-white dark:placeholder-gray-400"
					placeholder="Angabe weiterer Informationen"
				></textarea>
			</div>
			<button
				type="submit"
				class="btn-primary btn-md rounded-full border-3 border-fuchsia-500 bg-fuchsia-900/20 px-4
        py-1 inset-shadow-sm inset-shadow-fuchsia-950 dark:text-white dark:inset-shadow-fuchsia-300"
				>Anfrage absenden</button
			>
		</form>
	</div>
</section>
