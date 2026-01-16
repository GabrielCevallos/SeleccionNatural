import pygame
import random
import sys
import matplotlib.pyplot as plt

# Inicializar Pygame
pygame.init()

# ===== PARÁMETROS CONFIGURABLES DE LA SIMULACIÓN =====
ANCHO_VENTANA = 1000
ALTO_VENTANA = 750
MARGEN = 50
TAMANO_PASO = 20  # Tamaño de cada paso en píxeles
PASOS_POR_VIDA = 100  # Número de pasos que puede dar cada partícula
DURACION_DIA = 300  # Pasos del día (debe ser mucho mayor que PASOS_POR_VIDA)
PORCENTAJE_COMIDA = 20  # Porcentaje del mapa con comida (valor por defecto de menú)
PORCENTAJE_PARTICULAS_INICIAL = 10  # Porcentaje de comida que será partículas iniciales (por defecto)
NUM_DIAS = 30  # Número de días a simular (por defecto)
TAMANO_CELDA = 20  # Tamaño de cada celda de la cuadrícula

# Colores
NEGRO = (20, 20, 20)
BLANCO = (255, 255, 255)
GRIS = (100, 100, 100)
GRIS_OSCURO = (50, 50, 50)
AZUL_BOTON = (66, 165, 245)
VERDE = (76, 175, 80)
NARANJA = (255, 87, 34)
ROJO = (255, 0, 0)
AMARILLO = (255, 255, 0)
CYAN = (0, 255, 255)
COLORES_PARTICULAS = [
    (66, 165, 245),   # Azul
    (255, 87, 34),    # Naranja
    (102, 187, 106),  # Verde
    (171, 71, 188),   # Púrpura
    (255, 193, 7),    # Amarillo
    (0, 255, 255),    # Cyan
    (255, 105, 180),  # Rosa
    (255, 255, 0)     # Amarillo brillante
]


# UI simple
class Boton:
    def __init__(self, rect, texto, color_fondo, color_hover, color_texto=BLANCO):
        self.rect = pygame.Rect(rect)
        self.texto = texto
        self.color_fondo = color_fondo
        self.color_hover = color_hover
        self.color_texto = color_texto

    def dibujar(self, pantalla, fuente):
        color = self.color_hover if self.rect.collidepoint(pygame.mouse.get_pos()) else self.color_fondo
        pygame.draw.rect(pantalla, color, self.rect, border_radius=8)
        pygame.draw.rect(pantalla, BLANCO, self.rect, 2, border_radius=8)
        texto = fuente.render(self.texto, True, self.color_texto)
        texto_rect = texto.get_rect(center=self.rect.center)
        pantalla.blit(texto, texto_rect)

    def click(self, pos):
        return self.rect.collidepoint(pos)


class CampoTexto:
    def __init__(self, rect, valor_inicial="0"):
        self.rect = pygame.Rect(rect)
        self.texto = valor_inicial
        self.activo = False

    def manejar_evento(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN:
            self.activo = self.rect.collidepoint(evento.pos)
        if evento.type == pygame.KEYDOWN and self.activo:
            if evento.key == pygame.K_BACKSPACE:
                self.texto = self.texto[:-1]
            elif evento.key in (pygame.K_RETURN, pygame.K_TAB):
                self.activo = False
            elif evento.unicode.isdigit():
                self.texto = (self.texto + evento.unicode)[:4]

    def dibujar(self, pantalla, fuente):
        color_fondo = AZUL_BOTON if self.activo else GRIS_OSCURO
        pygame.draw.rect(pantalla, color_fondo, self.rect, border_radius=6)
        pygame.draw.rect(pantalla, BLANCO, self.rect, 2, border_radius=6)
        texto = self.texto if self.texto else "0"
        txt = fuente.render(texto, True, BLANCO)
        txt_rect = txt.get_rect(center=self.rect.center)
        pantalla.blit(txt, txt_rect)

    def valor(self, minimo=0, maximo=9999, defecto=0):
        try:
            v = int(self.texto) if self.texto else defecto
            return max(minimo, min(v, maximo))
        except ValueError:
            return defecto


class Slider:
    def __init__(self, x, y, ancho, minimo, maximo, valor_inicial):
        self.rect = pygame.Rect(x, y, ancho, 8)
        self.min = minimo
        self.max = maximo
        self.valor = valor_inicial
        self.handle_radius = 10
        self.arrastrando = False

    def _pos_a_valor(self, mouse_x):
        t = (mouse_x - self.rect.left) / self.rect.width
        t = max(0.0, min(1.0, t))
        return int(self.min + t * (self.max - self.min))

    def manejar_evento(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(evento.pos):
            self.arrastrando = True
            self.valor = self._pos_a_valor(evento.pos[0])
        elif evento.type == pygame.MOUSEBUTTONUP:
            self.arrastrando = False
        elif evento.type == pygame.MOUSEMOTION and self.arrastrando:
            self.valor = self._pos_a_valor(evento.pos[0])

    def dibujar(self, pantalla):
        pygame.draw.rect(pantalla, BLANCO, self.rect, border_radius=4)
        filled_w = int(self.rect.width * (self.valor - self.min) / (self.max - self.min))
        pygame.draw.rect(pantalla, VERDE, (self.rect.left, self.rect.top, filled_w, self.rect.height), border_radius=4)
        handle_x = self.rect.left + filled_w
        pygame.draw.circle(pantalla, AZUL_BOTON, (handle_x, self.rect.centery), self.handle_radius)


# Clase para representar una partícula con sistema de supervivencia
class Particula:
    def __init__(self, x, y, color, pasos_vida):
        self.x = x
        self.y = y
        self.pos_inicial = (x, y)  # Guardar posición inicial (casa)
        self.color = color
        self.pasos_vida = pasos_vida  # Pasos máximos por vida
        self.pasos_restantes = pasos_vida
        self.trayectoria = [(self.x, self.y)]
        self.activa = True
        self.en_casa = True
        self.veces_comido = 0
        self.ha_comido_hoy = False
        self.salio_de_casa = False
        self.debe_morir = False
        self.puede_reproducirse = False
        
    def esta_en_borde(self, limites):
        """Verifica si la partícula está en el borde (casa)"""
        return (self.x == limites['izq'] or self.x == limites['der'] or
                self.y == limites['arr'] or self.y == limites['abaj'])
    
    def mover(self, limites):
        """Mueve la partícula un paso usando Simple Random Walk"""
        if self.pasos_restantes <= 0 or not self.activa:
            return False
        
        direcciones = [
            (TAMANO_PASO, 0),      # Derecha
            (-TAMANO_PASO, 0),     # Izquierda
            (0, TAMANO_PASO),      # Abajo
            (0, -TAMANO_PASO)      # Arriba
        ]
        
        # Elegir dirección aleatoria y mover
        dx, dy = random.choice(direcciones)
        nuevo_x = max(limites['izq'], min(self.x + dx, limites['der']))
        nuevo_y = max(limites['arr'], min(self.y + dy, limites['abaj']))
        
        self.x = nuevo_x
        self.y = nuevo_y
        self.trayectoria.append((self.x, self.y))
        self.pasos_restantes -= 1
        
        # Verificar si está en casa
        if self.esta_en_borde(limites):
            self.en_casa = True
        else:
            self.en_casa = False
            if not self.salio_de_casa:
                self.salio_de_casa = True
        
        return True
    
    def intentar_comer(self, comida_pos):
        """Intenta comer si hay comida en la posición actual"""
        if (self.x, self.y) in comida_pos:
            self.veces_comido += 1
            self.ha_comido_hoy = True
            comida_pos.remove((self.x, self.y))
            return True
        return False
    
    def reiniciar_dia(self, limites):
        """Reinicia la partícula para el siguiente día"""
        # Generar nueva posición en el borde
        self.x, self.y = generar_posicion_borde(limites)
        self.pos_inicial = (self.x, self.y)
        self.pasos_restantes = self.pasos_vida
        self.trayectoria = [(self.x, self.y)]
        self.en_casa = True
        self.veces_comido = 0
        self.ha_comido_hoy = False
        self.salio_de_casa = False
        self.activa = True
        self.puede_reproducirse = False
        
    def dibujar(self, pantalla, mostrar_trayectoria=False):
        """Dibuja la partícula"""
        if mostrar_trayectoria and len(self.trayectoria) > 1:
            pygame.draw.lines(pantalla, self.color, False, self.trayectoria, 1)
        
        # Dibujar la partícula
        pygame.draw.circle(pantalla, self.color, (self.x, self.y), 4)
        
        # Si está en casa, dibujar un círculo alrededor
        if self.en_casa:
            pygame.draw.circle(pantalla, VERDE, (self.x, self.y), 7, 2)


# Funciones auxiliares
def generar_posicion_borde(limites):
    """Genera una posición aleatoria en el borde (casa)"""
    borde = random.choice(['izq', 'der', 'arr', 'abaj'])
    
    if borde == 'izq':
        x = limites['izq']
        y = random.randrange(limites['arr'], limites['abaj'] + 1, TAMANO_PASO)
    elif borde == 'der':
        x = limites['der']
        y = random.randrange(limites['arr'], limites['abaj'] + 1, TAMANO_PASO)
    elif borde == 'arr':
        x = random.randrange(limites['izq'], limites['der'] + 1, TAMANO_PASO)
        y = limites['arr']
    else:  # 'abaj'
        x = random.randrange(limites['izq'], limites['der'] + 1, TAMANO_PASO)
        y = limites['abaj']
    
    return x, y


def generar_comida(limites, porcentaje):
    """Genera posiciones de comida en el mapa"""
    # Calcular dimensiones de la cuadrícula
    ancho = (limites['der'] - limites['izq']) // TAMANO_PASO + 1
    alto = (limites['abaj'] - limites['arr']) // TAMANO_PASO + 1
    total_celdas = ancho * alto
    
    # Calcular número de comidas
    num_comidas = int(total_celdas * porcentaje / 100)
    
    # Generar todas las posiciones posibles
    todas_posiciones = []
    for x in range(limites['izq'], limites['der'] + 1, TAMANO_PASO):
        for y in range(limites['arr'], limites['abaj'] + 1, TAMANO_PASO):
            # Excluir bordes (casa)
            if x != limites['izq'] and x != limites['der'] and y != limites['arr'] and y != limites['abaj']:
                todas_posiciones.append((x, y))
    
    # Seleccionar aleatoriamente
    comida = set(random.sample(todas_posiciones, min(num_comidas, len(todas_posiciones))))
    return comida


def crear_particulas_iniciales(limites, num_particulas, pasos_vida):
    """Crea las partículas iniciales en posiciones aleatorias del borde"""
    particulas = []
    for i in range(num_particulas):
        x, y = generar_posicion_borde(limites)
        color = COLORES_PARTICULAS[i % len(COLORES_PARTICULAS)]
        particula = Particula(x, y, color, pasos_vida)
        particulas.append(particula)
    return particulas


def dibujar_paredes(pantalla, limites):
    """Dibuja las paredes del ambiente"""
    ancho = limites['der'] - limites['izq']
    alto = limites['abaj'] - limites['arr']
    pygame.draw.rect(pantalla, BLANCO, (limites['izq'], limites['arr'], ancho, alto), 3)
    
    # Resaltar que el borde es la casa
    pygame.draw.rect(pantalla, VERDE, (limites['izq'], limites['arr'], ancho, alto), 1)


def dibujar_cuadricula(pantalla, limites):
    """Dibuja la cuadrícula del ambiente"""
    # Líneas verticales
    for x in range(limites['izq'], limites['der'] + 1, TAMANO_CELDA):
        pygame.draw.line(pantalla, GRIS, (x, limites['arr']), (x, limites['abaj']), 1)
    
    # Líneas horizontales
    for y in range(limites['arr'], limites['abaj'] + 1, TAMANO_CELDA):
        pygame.draw.line(pantalla, GRIS, (limites['izq'], y), (limites['der'], y), 1)


def dibujar_comida(pantalla, comida_pos):
    """Dibuja la comida en el mapa"""
    for x, y in comida_pos:
        pygame.draw.circle(pantalla, AMARILLO, (x, y), 3)
        pygame.draw.circle(pantalla, NARANJA, (x, y), 5, 1)


def dibujar_muerte(pantalla, pos, frames_restantes):
    """Pequeña animación de muerte en rojo"""
    x, y = pos
    escala = max(4, 2 * frames_restantes)
    color = (255, 80, 80)
    pygame.draw.circle(pantalla, color, (x, y), escala, 2)
    pygame.draw.line(pantalla, color, (x - escala, y - escala), (x + escala, y + escala), 2)
    pygame.draw.line(pantalla, color, (x - escala, y + escala), (x + escala, y - escala), 2)


def pantalla_configuracion(pantalla, reloj):
    """Pantalla inicial para configurar días, partículas y % comida"""
    fuente_titulo = pygame.font.Font(None, 64)
    fuente = pygame.font.Font(None, 32)
    fuente_small = pygame.font.Font(None, 24)

    campo_dias = CampoTexto((ANCHO_VENTANA//2 + 100, 260, 120, 45), str(NUM_DIAS))
    campo_particulas = CampoTexto((ANCHO_VENTANA//2 + 100, 330, 120, 45), "50")
    campo_comida = CampoTexto((ANCHO_VENTANA//2 + 100, 400, 120, 45), str(PORCENTAJE_COMIDA))
    campo_pasos = CampoTexto((ANCHO_VENTANA//2 + 100, 470, 120, 45), str(PASOS_POR_VIDA))

    boton_iniciar = Boton((ANCHO_VENTANA//2 - 160, 560, 150, 60), "INICIAR", VERDE, (102, 187, 106))
    boton_salir = Boton((ANCHO_VENTANA//2 + 20, 560, 150, 60), "SALIR", ROJO, (200, 50, 50))

    corriendo = True
    while corriendo:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            campo_dias.manejar_evento(evento)
            campo_particulas.manejar_evento(evento)
            campo_comida.manejar_evento(evento)
            campo_pasos.manejar_evento(evento)

            if evento.type == pygame.MOUSEBUTTONDOWN:
                if boton_iniciar.click(evento.pos):
                    return {
                        "dias": campo_dias.valor(minimo=1, maximo=999, defecto=NUM_DIAS),
                        "particulas": campo_particulas.valor(minimo=1, maximo=2000, defecto=50),
                        "comida": campo_comida.valor(minimo=1, maximo=90, defecto=PORCENTAJE_COMIDA),
                        "pasos": campo_pasos.valor(minimo=10, maximo=500, defecto=PASOS_POR_VIDA)
                    }
                if boton_salir.click(evento.pos):
                    pygame.quit()
                    sys.exit()

        pantalla.fill(NEGRO)
        titulo = fuente_titulo.render("Configurar Simulación", True, AZUL_BOTON)
        pantalla.blit(titulo, titulo.get_rect(center=(ANCHO_VENTANA//2, 120)))

        labels = ["Número de días", "Partículas iniciales", "% de comida en mapa", "Pasos por vida"]
        campos = [campo_dias, campo_particulas, campo_comida, campo_pasos]
        y_base = 260
        for i, (lbl, campo) in enumerate(zip(labels, campos)):
            texto = fuente.render(lbl + ":", True, BLANCO)
            pantalla.blit(texto, (ANCHO_VENTANA//2 - 220, y_base + i*70))
            campo.dibujar(pantalla, fuente)

        info_lines = [
            "ESPACIO pausar (ya en simulación)",
            "Botón PAUSAR en pantalla de simulación",
            "Reinicio disponible dentro de la simulación",
            "Velocidad controlada con barra deslizante"
        ]
        for i, ln in enumerate(info_lines):
            t = fuente_small.render(ln, True, GRIS)
            pantalla.blit(t, (ANCHO_VENTANA//2 - 220, 680 + i*26))

        boton_iniciar.dibujar(pantalla, fuente)
        boton_salir.dibujar(pantalla, fuente)

        pygame.display.flip()
        reloj.tick(60)


def simulacion(pantalla, reloj, num_dias, pasos_vida, duracion_dia, porcentaje_comida, num_particulas_inicial):
    """Ejecuta la simulación de selección natural por varios días"""
    fuente_grande = pygame.font.Font(None, 40)
    fuente = pygame.font.Font(None, 28)
    fuente_pequena = pygame.font.Font(None, 22)

    # Definir límites del mundo
    limites = {
        'izq': MARGEN,
        'der': ANCHO_VENTANA - MARGEN - 300,  # Espacio para panel lateral
        'arr': MARGEN + 100,
        'abaj': ALTO_VENTANA - MARGEN
    }

    # Botones y slider
    boton_pausa = Boton((ANCHO_VENTANA - 260, 20, 70, 40), "PAUSA", AZUL_BOTON, (90, 190, 255))
    boton_reiniciar = Boton((ANCHO_VENTANA - 180, 20, 80, 40), "RESET", NARANJA, (255, 140, 60))
    boton_menu = Boton((ANCHO_VENTANA - 90, 20, 60, 40), "MENU", ROJO, (200, 50, 50))
    slider_vel = Slider(ANCHO_VENTANA - 260, 70, 210, 5, 120, 30)

    def reset_state():
        part = crear_particulas_iniciales(limites, num_particulas_inicial, pasos_vida)
        food = generar_comida(limites, porcentaje_comida)
        return part, food, [len(part)], 1, 0, False, slider_vel.valor

    particulas, comida_pos, historial_poblacion, dia_actual, paso_actual_dia, pausado, velocidad = reset_state()
    mostrar_trayectorias = False
    anim_muertes = []  # lista de {'pos': (x,y), 'frames': n}

    corriendo = True
    while corriendo and dia_actual <= num_dias:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    return historial_poblacion
                elif evento.key == pygame.K_SPACE:
                    pausado = not pausado
                elif evento.key == pygame.K_t:
                    mostrar_trayectorias = not mostrar_trayectorias
            slider_vel.manejar_evento(evento)
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if boton_pausa.click(evento.pos):
                    pausado = not pausado
                if boton_reiniciar.click(evento.pos):
                    particulas, comida_pos, historial_poblacion, dia_actual, paso_actual_dia, pausado, velocidad = reset_state()
                    anim_muertes.clear()
                if boton_menu.click(evento.pos):
                    return None

        velocidad = slider_vel.valor

        # Simulación del día
        if not pausado and paso_actual_dia < duracion_dia:
            for particula in particulas:
                if particula.activa and particula.pasos_restantes > 0:
                    particula.mover(limites)

                    # Regla 9: Intentar comer si hay comida
                    if not particula.en_casa:
                        if (particula.x, particula.y) in comida_pos:
                            particulas_en_comida = [p for p in particulas if p.x == particula.x and p.y == particula.y]
                            if len(particulas_en_comida) > 1:
                                if random.choice(particulas_en_comida) == particula:
                                    particula.intentar_comer(comida_pos)
                            else:
                                particula.intentar_comer(comida_pos)

                    # Regla 19: Si regresó a casa y comió, se queda
                    # Regla 10: Si regresó sin comer pero con pasos, debe salir de nuevo
                    if particula.en_casa and particula.salio_de_casa:
                        if particula.ha_comido_hoy:
                            # Regla 19: Se queda en casa
                            particula.activa = False
                            if particula.veces_comido >= 2:
                                particula.puede_reproducirse = True
                        elif particula.pasos_restantes > 0:
                            # Regla 10: Debe salir de nuevo
                            particula.en_casa = False
                
                # Regla 5: Si salió de casa y se quedó sin pasos fuera de casa, muere INMEDIATAMENTE
                elif particula.salio_de_casa and not particula.en_casa and particula.pasos_restantes <= 0:
                    if particula.activa:
                        particula.activa = False
                        particula.debe_morir = True
                        anim_muertes.append({"pos": (particula.x, particula.y), "frames": 15})

            paso_actual_dia += 1

        # Fin de día
        if paso_actual_dia >= duracion_dia and not pausado:
            sobrevivientes = []
            nuevas_particulas = []

            for particula in particulas:
                # Regla 3: Sobrevive SI Y SOLO SI comió al menos 1 vez Y regresó a casa
                # En cualquier otro caso (no comió O no regresó) = muere
                sobrevive = particula.ha_comido_hoy and particula.en_casa

                if sobrevive:
                    sobrevivientes.append(particula)
                    # Regla 7: Si comió 2+ veces, se reproduce
                    if particula.puede_reproducirse:
                        x, y = generar_posicion_borde(limites)
                        color = random.choice(COLORES_PARTICULAS)
                        hijo = Particula(x, y, color, pasos_vida)
                        nuevas_particulas.append(hijo)
                else:
                    # Solo agregar animación si no murió durante el día (Regla 5)
                    if not particula.debe_morir:
                        anim_muertes.append({"pos": (particula.x, particula.y), "frames": 15})

            particulas = sobrevivientes + nuevas_particulas

            if len(particulas) == 0:
                historial_poblacion.append(0)
                break

            for p in particulas:
                p.reiniciar_dia(limites)

            comida_pos = generar_comida(limites, porcentaje_comida)
            historial_poblacion.append(len(particulas))
            dia_actual += 1
            paso_actual_dia = 0

        # Dibujar
        pantalla.fill(NEGRO)

        pygame.draw.rect(pantalla, GRIS_OSCURO, (0, 0, ANCHO_VENTANA, 100))
        pygame.draw.line(pantalla, BLANCO, (0, 100), (ANCHO_VENTANA, 100), 2)

        texto_dia = fuente_grande.render(f"DÍA {dia_actual}/{num_dias}", True, CYAN)
        pantalla.blit(texto_dia, (20, 20))

        texto_poblacion = fuente_grande.render(f"Población: {len(particulas)}", True, VERDE)
        pantalla.blit(texto_poblacion, (320, 20))

        texto_comida = fuente.render(f"Comida: {len(comida_pos)}", True, AMARILLO)
        pantalla.blit(texto_comida, (320, 60))

        if pausado:
            texto_pausa = fuente.render("⏸ PAUSADO", True, ROJO)
            pantalla.blit(texto_pausa, (ANCHO_VENTANA - 450, 30))

        boton_pausa.dibujar(pantalla, fuente)
        boton_reiniciar.dibujar(pantalla, fuente)
        boton_menu.dibujar(pantalla, fuente)
        slider_vel.dibujar(pantalla)
        texto_vel = fuente_pequena.render(f"Velocidad: {velocidad} FPS", True, BLANCO)
        pantalla.blit(texto_vel, (ANCHO_VENTANA - 255, 82))

        dibujar_cuadricula(pantalla, limites)
        dibujar_paredes(pantalla, limites)
        dibujar_comida(pantalla, comida_pos)

        for particula in particulas:
            particula.dibujar(pantalla, mostrar_trayectorias)

        for anim in list(anim_muertes):
            dibujar_muerte(pantalla, anim["pos"], anim["frames"])
            anim["frames"] -= 1
            if anim["frames"] <= 0:
                anim_muertes.remove(anim)

        panel_x = ANCHO_VENTANA - 280
        pygame.draw.rect(pantalla, GRIS_OSCURO, (panel_x, 100, 280, ALTO_VENTANA - 100))
        pygame.draw.line(pantalla, BLANCO, (panel_x, 100), (panel_x, ALTO_VENTANA), 2)

        y_pos = 120
        lineas_panel = [
            "ESTADÍSTICAS",
            f"Partículas vivas: {len([p for p in particulas if p.activa])}",
            f"En casa: {len([p for p in particulas if p.en_casa])}",
            f"Comieron hoy: {len([p for p in particulas if p.ha_comido_hoy])}",
            f"Pueden reproducirse: {len([p for p in particulas if p.puede_reproducirse])}",
            "",
            "CONTROLES",
            "ESPACIO / Botón: Pausa",
            "T: Trayectorias",
            "ESC: Salir",
            "",
            "Reiniciar: Botón"
        ]

        for i, linea in enumerate(lineas_panel):
            if i == 0 or i == 6:
                color = CYAN
                fuente_usar = fuente
            else:
                color = BLANCO
                fuente_usar = fuente_pequena

            texto = fuente_usar.render(linea, True, color)
            pantalla.blit(texto, (panel_x + 10, y_pos + i * 30))

        pygame.display.flip()
        reloj.tick(velocidad)

    return historial_poblacion


def mostrar_grafica_poblacion(historial_poblacion):
    """Muestra una gráfica de la evolución de la población"""
    plt.figure(figsize=(10, 6))
    plt.plot(range(len(historial_poblacion)), historial_poblacion, marker='o', 
             linewidth=2, markersize=6, color='#42A5F5')
    plt.xlabel('Día', fontsize=12)
    plt.ylabel('Población', fontsize=12)
    plt.title('Evolución de la Población a lo Largo del Tiempo', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


def main():
    """Función principal"""
    pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
    pygame.display.set_caption("Simulación de Selección Natural")
    reloj = pygame.time.Clock()

    while True:
        config = pantalla_configuracion(pantalla, reloj)

        # Ejecutar simulación
        historial = simulacion(
            pantalla,
            reloj,
            config["dias"],
            config["pasos"],
            DURACION_DIA,
            config["comida"],
            config["particulas"],
        )
        
        # Si historial es None, el usuario quiere volver al menú
        if historial is None:
            continue
        
        # Si llegamos aquí, la simulación terminó naturalmente
        pygame.quit()
        
        # Mostrar gráfica de evolución
        print("\n=== RESULTADOS DE LA SIMULACIÓN ===")
        print(f"Población inicial: {historial[0]}")
        print(f"Población final: {historial[-1]}")
        print(f"Población máxima: {max(historial)}")
        print(f"Población mínima: {min(historial)}")
        print("====================================\n")
        
        mostrar_grafica_poblacion(historial)
        break


if __name__ == "__main__":
    main()
