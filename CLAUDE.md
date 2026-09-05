# Viewy

Viewy es un tracker personal de contenido multimedia creado como proyecto de portfolio.

La aplicación permitirá a cada usuario registrar y gestionar películas, series y anime que:

- ha visto
- está viendo
- quiere ver
- ha abandonado

El objetivo del proyecto no es únicamente construir una aplicación funcional, sino también aprender y practicar de forma realista distintas tecnologías y conceptos de desarrollo backend, bases de datos, análisis de datos, frontend e inteligencia artificial.

---

## Idioma

Respóndeme siempre en español.

Las explicaciones, decisiones técnicas, revisiones y comentarios pedagógicos deben estar en español.

El código debe seguir convenciones profesionales, utilizando inglés cuando sea lo habitual para:

- nombres de variables
- funciones
- clases
- modelos
- apps de Django
- endpoints
- nombres de archivos
- nombres de tablas
- mensajes de commit
- nombres de servicios
- nombres de funciones auxiliares

No traduzcas términos técnicos cuando hacerlo los vuelva menos claros.

---

## Objetivo del proyecto

Quiero construir una aplicación web real que pueda enseñar en mi portfolio.

La aplicación debe tener una arquitectura limpia, profesional y entendible.

No quiero una demo simple ni un CRUD básico sin más.

Quiero que el proyecto me permita demostrar conocimientos de:

- Python
- Django
- Django ORM
- MySQL
- diseño de bases de datos
- autenticación de usuarios
- HTML
- Tailwind CSS
- JavaScript
- consumo de APIs externas
- pandas
- DataFrames
- análisis de datos
- visualización de estadísticas
- integración con LLM
- testing
- Docker
- Docker Compose
- variables de entorno
- buenas prácticas de arquitectura
- Git
- despliegue
- documentación técnica

---

## Stack principal

El stack previsto es:

- Python
- Django
- Django ORM
- MySQL
- HTML
- Tailwind CSS
- JavaScript
- pandas
- APIs externas
- integración con LLM
- Docker
- Docker Compose
- Pytest
- Git
- GitHub

No añadas tecnologías o dependencias nuevas si no están justificadas.

---

## Reglas de trabajo

Este proyecto es también un proyecto de aprendizaje.

NO construyas grandes partes de la aplicación de una sola vez.

Trabaja siempre fase por fase.

No avances automáticamente.

Antes de implementar una fase:

1. analiza el estado actual del proyecto
2. explica qué vamos a construir
3. explica por qué se va a construir así
4. indica qué archivos se van a crear o modificar
5. explica los conceptos importantes de Django/Python implicados
6. señala posibles decisiones de arquitectura que haya que tomar
7. si hay varias opciones razonables, compáralas antes de elegir

Después de implementar una fase:

1. comprueba que el código funciona
2. revisa posibles errores
3. explica qué se ha creado
4. dime cómo probarlo manualmente
5. propón tests relevantes
6. resume qué conceptos he aprendido
7. DETENTE

No continúes a la siguiente fase hasta que yo lo pida explícitamente.

---

## Filosofía de desarrollo

Prefiere siempre soluciones:

- simples
- profesionales
- fáciles de mantener
- fáciles de entender
- razonables para un proyecto de portfolio

Evita:

- sobrearquitectura
- abstracciones innecesarias
- patrones complejos sin beneficio real
- añadir librerías por comodidad si Django ya resuelve el problema
- meter toda la lógica en views.py
- crear demasiadas capas sin necesidad
- grandes refactors sin explicación previa

Si detectas una decisión incorrecta o mejorable, explícame el motivo antes de cambiarla.

---

## Git y seguridad

Nunca subas ni incluyas en Git:

- contraseñas
- API keys
- tokens
- secretos
- credenciales de base de datos
- archivos .env
- claves privadas

Utiliza variables de entorno para cualquier secreto.

Mantén un archivo `.env.example` cuando tenga sentido.

Los commits deben ser pequeños, claros y profesionales.

Usa mensajes de commit en inglés.

Ejemplos:

- `chore: initialize Django project`
- `feat: add user authentication`
- `feat: add media library models`
- `fix: restrict library items to owner`
- `test: add authentication tests`

---

## Arquitectura prevista

El proyecto tendrá progresivamente apps de Django como:

- accounts
- library
- analytics
- recommendations
- integrations

La estructura puede cambiar si encontramos una opción mejor.

No fuerces esta arquitectura si todavía no hace falta.

---

## Separación de responsabilidades

No concentres toda la lógica de negocio en `views.py`.

Utiliza:

- models para estructura y comportamiento del dominio
- forms para validación de formularios
- views para manejar request/response
- services para lógica de negocio o integraciones externas cuando tenga sentido
- utils únicamente para funciones auxiliares realmente genéricas
- templates para presentación
- tests para comportamiento esperado

No crees services vacíos o innecesarios solo por seguir una arquitectura.

---

## Base de datos

La base de datos principal será MySQL.

Quiero aprender a trabajar con una base de datos relacional real.

Al principio se puede utilizar SQLite si facilita el arranque del proyecto, pero el objetivo final es utilizar MySQL.

Cuando llegue el momento de introducir MySQL:

- explica la configuración
- explica la conexión con Django
- explica las variables de entorno
- explica cómo manejar migraciones
- explica cómo usarlo con Docker

No cambies de base de datos sin explicarme antes el motivo.

---

## Frontend y diseño

El diseño visual lo decidiré yo.

Utilizaremos Tailwind CSS como sistema principal de estilos.

Puedo proporcionar diseños hechos en Lovable o referencias similares.

Claude no debe rediseñar la aplicación por iniciativa propia.

Cuando trabajemos en frontend:

- respeta el diseño que yo proporcione
- adapta los templates de Django al diseño existente
- utiliza HTML semántico
- utiliza Tailwind CSS
- evita Bootstrap
- evita frameworks frontend adicionales sin justificación
- mantén JavaScript sencillo siempre que sea posible
- no introduzcas React, Vue o similares salvo que exista una razón técnica clara y yo lo apruebe

---

## Funcionalidades finales deseadas

Cada usuario podrá:

- registrarse
- iniciar sesión
- cerrar sesión
- tener su propio perfil
- buscar contenido
- añadir películas
- añadir series
- añadir anime
- marcar contenido como pendiente
- marcar contenido como viendo
- marcar contenido como terminado
- marcar contenido como abandonado
- puntuar contenido
- escribir reseñas
- guardar fecha de inicio
- guardar fecha de finalización
- guardar progreso de episodios
- marcar favoritos
- filtrar su biblioteca
- ordenar su biblioteca
- buscar dentro de su biblioteca
- consultar estadísticas
- recibir recomendaciones mediante IA
- hacer preguntas sobre su propio historial

Cada usuario debe poder acceder únicamente a sus propios registros personales.

---

## Modelo de datos previsto

La idea inicial es diferenciar entre el contenido y la relación del contenido con cada usuario.

Ejemplo:

### MediaItem

Campos aproximados:

- id
- title
- media_type
- release_year
- description
- genres
- poster
- external_id
- external_source
- duration
- episodes
- created_at
- updated_at

### UserMedia

Campos aproximados:

- user
- media
- status
- rating
- review
- started_at
- finished_at
- current_episode
- favorite
- created_at
- updated_at

Una misma película, serie o anime debe poder existir una sola vez en `MediaItem` y estar asociada a varios usuarios mediante `UserMedia`.

Este diseño se puede modificar si encontramos una solución mejor.

---

## Estados previstos

Los estados principales serán:

- planned
- watching
- completed
- dropped

Los nombres internos deben estar en inglés.

La interfaz podrá mostrarlos en español.

---

## APIs externas

Más adelante quiero integrar APIs externas para no introducir manualmente toda la información.

Para películas y series podemos estudiar:

- TMDB

Para anime podemos estudiar una API adecuada cuando lleguemos a esa fase.

No integres estas APIs antes de llegar a la fase correspondiente.

La lógica de APIs externas debe estar separada del resto de la aplicación.

---

## Pandas

Quiero utilizar pandas de forma real y justificada.

No quiero importar pandas únicamente para poder decir que el proyecto lo usa.

Quiero utilizar DataFrames para análisis de datos cuando tenga sentido.

Ejemplos de análisis:

- nota media
- contenido visto por año
- contenido visto por mes
- géneros favoritos
- géneros mejor puntuados
- películas vistas
- series vistas
- anime vistos
- títulos terminados
- títulos abandonados
- horas aproximadas vistas
- rankings
- evolución temporal
- hábitos del usuario
- comparaciones entre tipos de contenido

Cuando lleguemos a esta fase, explica qué cálculos tienen más sentido con Django ORM y cuáles con pandas.

No utilices pandas si una consulta simple de Django ORM es claramente mejor.

---

## Inteligencia artificial y LLM

La IA será una fase avanzada.

No quiero empezar el proyecto por la IA.

Quiero que la IA aporte valor real.

No quiero meter un chatbot genérico sin relación con los datos del usuario.

---

## Recomendaciones personalizadas

El sistema podrá utilizar el historial del usuario para generar recomendaciones.

Ejemplo:

El usuario pregunta:

`Recomiéndame una serie corta`

El backend podrá obtener información como:

- géneros favoritos
- contenido mejor puntuado
- contenido visto recientemente
- duración media preferida
- tipos de contenido favoritos

Después se enviará al LLM únicamente el contexto necesario.

El LLM no debe recibir datos innecesarios.

---

## Chat con la biblioteca

Quiero poder hacer preguntas como:

- ¿Qué género puntúo mejor?
- ¿Qué he visto este año?
- ¿Qué anime terminé el año pasado?
- ¿Cuál fue mi mes con más películas?
- ¿Qué director parece gustarme más?
- Recomiéndame algo corto para este fin de semana
- ¿Qué tipo de contenido veo más?

Siempre que una pregunta pueda resolverse mediante:

- Django ORM
- SQL
- Python
- pandas

primero se deben calcular los datos mediante código.

El LLM debe utilizarse principalmente para:

- interpretar lenguaje natural
- decidir qué datos necesita
- generar una respuesta natural
- resumir resultados

El LLM no debe inventar cálculos que podemos obtener directamente de la base de datos.

---

## Importación inteligente

Quiero poder importar en el futuro listas antiguas desde texto.

Ejemplo:

Breaking Bad 9
Dark 9
One Piece 8
Interstellar 10

El sistema podrá convertir ese texto en datos estructurados.

Antes de guardar definitivamente la información:

- mostrar una vista previa
- permitir corregir errores
- confirmar la importación

---

# Roadmap de desarrollo

## Fase 0 — Preparación del proyecto

Objetivo:

Preparar correctamente el proyecto.

Incluye:

- comprobar versión de Python
- crear entorno virtual
- instalar Django
- crear requirements
- crear `.gitignore`
- preparar variables de entorno
- crear `.env.example`
- crear proyecto Django
- configuración inicial
- revisar Git
- comprobar conexión con GitHub

No implementar funcionalidades reales.

No avanzar a la Fase 1.

---

## Fase 1 — Estructura básica de Django

Objetivo:

Entender la estructura básica del proyecto.

Incluye:

- settings
- urls
- templates
- static
- página inicial
- estructura inicial
- creación de las primeras apps si corresponde

Apps iniciales previstas:

- accounts
- library

---

## Fase 2 — Usuarios

Implementar:

- registro
- login
- logout
- perfil básico
- autenticación
- autorización

Analizar si conviene utilizar `CustomUser` desde el principio.

Explicar ventajas e inconvenientes antes de decidir.

---

## Fase 3 — Base de datos multimedia

Diseñar e implementar:

- MediaItem
- UserMedia

Crear:

- modelos
- migraciones
- relaciones
- restricciones
- validaciones básicas

Utilizar Django Admin para probar los modelos.

Todavía no integrar APIs externas.

---

## Fase 4 — CRUD de biblioteca

Permitir:

- añadir contenido manualmente
- editar contenido personal
- eliminar contenido personal
- cambiar estado
- puntuar
- escribir reseñas
- marcar favorito

Cada usuario únicamente podrá acceder a sus propios registros.

Revisar especialmente permisos y seguridad.

---

## Fase 5 — Interfaz de biblioteca

Crear una interfaz usable.

Añadir:

- listado
- tarjetas o tabla
- búsqueda
- filtros
- ordenación
- paginación

Filtros previstos:

- todos
- viendo
- terminados
- pendientes
- abandonados
- favoritos

El diseño se adaptará al diseño visual que yo proporcione.

---

## Fase 6 — API externa de películas y series

Integrar una API externa.

Flujo aproximado:

buscar título
→ consultar API
→ mostrar resultados
→ seleccionar uno
→ crear o reutilizar MediaItem
→ crear UserMedia

Evitar duplicados.

Separar la integración externa mediante services.

---

## Fase 7 — Anime

Añadir soporte adecuado para anime.

Estudiar:

- qué API utilizar
- cómo mapear datos externos
- cómo gestionar episodios
- diferencias con películas y series

No duplicar modelos sin necesidad.

---

## Fase 8 — Dashboard de estadísticas

Crear una app `analytics`.

Mostrar estadísticas básicas usando Django ORM.

Ejemplos:

- total visto
- total pendiente
- total terminado
- nota media
- favoritos
- distribución por tipo

Todavía sin pandas si no es necesario.

---

## Fase 9 — Pandas y DataFrames

Introducir pandas para análisis más avanzado.

Crear DataFrames a partir de QuerySets.

Analizar:

- puntuaciones
- géneros
- evolución temporal
- tipos de contenido
- horas vistas
- hábitos
- rankings

Comparar ORM frente a pandas.

---

## Fase 10 — Gráficas

Visualizar estadísticas.

Podemos estudiar opciones como:

- Chart.js

No añadir una librería gráfica compleja si una opción ligera es suficiente.

---

## Fase 11 — Recomendaciones con LLM

Crear la app:

- recommendations

Integrar un proveedor de LLM mediante una capa desacoplada.

Nunca almacenar API keys directamente en código.

Crear primero una funcionalidad sencilla de recomendación.

---

## Fase 12 — Asistente inteligente

Permitir preguntas sobre la biblioteca.

Arquitectura aproximada:

pregunta del usuario
→ interpretación
→ consulta Django ORM / pandas
→ datos estructurados
→ LLM
→ respuesta

Evitar enviar toda la base de datos innecesariamente al modelo.

---

## Fase 13 — Importación de listas antiguas

Permitir pegar texto antiguo.

Transformarlo en datos estructurados.

Mostrar una pantalla de confirmación antes de guardar.

Permitir corregir coincidencias incorrectas.

---

## Fase 14 — Tests

Añadir tests relevantes para:

- modelos
- autenticación
- permisos
- CRUD
- formularios
- services
- APIs externas
- recomendaciones
- analytics

Utilizar Pytest si encaja correctamente con el proyecto.

No crear tests triviales sin valor.

---

## Fase 15 — MySQL, Docker y producción

Preparar:

- MySQL
- Docker
- Docker Compose
- variables de entorno
- configuración de producción
- DEBUG
- static files
- logging
- conexión entre contenedores
- migraciones
- despliegue

Explicar Docker desde cero porque no he trabajado anteriormente con Docker.

Explicar:

- imágenes
- contenedores
- Dockerfile
- docker-compose.yml
- volumes
- ports
- networks
- variables de entorno

No asumir que ya conozco Docker.

---

## Fase 16 — Portfolio

Preparar un README profesional.

Debe explicar:

- nombre del proyecto
- problema que resuelve
- funcionalidades
- arquitectura
- tecnologías
- instalación
- capturas
- decisiones técnicas
- modelo de datos
- uso de pandas
- integración con IA
- tests
- Docker
- despliegue

El README debe estar orientado a portfolio y recruiters técnicos.

---

## Forma de enseñarme

Quiero que actúes como un desarrollador senior que me acompaña durante el proyecto.

Quiero aprender, no únicamente recibir código generado.

Cuando aparezca algo importante, explícame conceptos como:

- request
- response
- urls
- views
- templates
- models
- QuerySets
- migrations
- ForeignKey
- ManyToMany
- OneToOne
- autenticación
- autorización
- permisos
- formularios
- CBV
- FBV
- managers
- services
- middleware
- settings
- variables de entorno
- testing
- Docker
- MySQL
- APIs
- pandas
- DataFrames
- LLM

No quiero una explicación gigantesca de cada línea.

Quiero entender:

- qué hace
- por qué existe
- por qué elegimos esa solución
- qué alternativas había
- qué consecuencias tiene

---

## Primera tarea

Empieza únicamente por la FASE 0.

Antes de ejecutar o crear nada:

1. analiza el repositorio/directorio actual
2. dime qué situación tenemos
3. propón exactamente qué vamos a hacer en la FASE 0
4. dime qué archivos se crearán o modificarán
5. dime la estructura de archivos que tendremos al terminar
6. explícame qué conceptos voy a aprender en esta fase

No avances todavía a la FASE 1.

No hagas cambios hasta haber explicado primero el plan.