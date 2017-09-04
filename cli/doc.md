
## URL: https://twitter.com/i/profiles/show/<user>/timeline/tweets

  - Max position: 903449933658722305 (el más nuevo => el de más arriba)
  - Min position: 902570462441496576 (el más antiguo => el de más abajo)

## Ejemplo de actualización:

  - Cargar tweets más antiguos USANDO **MAX POSITION**:
	https://twitter.com/i/profiles/show/malwareunicorn/timeline/tweets?include_available_features=1&include_entities=1&max_position=903449933658722305&reset_error_state=false

	* Respuesta JSON:
		* min_position
		* has_more_items
		* items_html
		* new_latent_count

  - Cargar tweets más nuevos (útil para polling) **USANDO MIN POSITION**:
	https://twitter.com/i/profiles/show/malwareunicorn/timeline/tweets?composed_count=0&include_available_features=1&include_entities=1&include_new_items_bar=true&interval=30000&latent_count=0&min_position=903449933658722305

	* Respuesta JSON:
		* min_position
		* has_more_items
		* items_html
		* new_latent_count

