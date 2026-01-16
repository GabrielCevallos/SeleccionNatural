import pygame
import random
import sys
import matplotlib.pyplot as plt

# Inicializar Pygame
pygame.init()

#  PARÁMETROS CONFIGURABLES DE LA SIMULACIÓN 
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
# Colores por tipo de mutación
COLOR_NORMAL = (255, 255, 255)  # Blanco - Tipo normal
COLOR_MUTACION_VELOCIDAD = (255, 0, 0)  # Rojo - Velocidad aumentada
COLOR_MUTACION_PRIORIDAD = (0, 255, 0)  # Verde - Prioridad para comer


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
    def __init__(self, x, y, pasos_vida, tipo_mutacion="normal"):
        self.x = x
        self.y = y
        self.pos_inicial = (x, y)  # Guardar posición inicial (casa)
        self.tipo_mutacion = tipo_mutacion  # "normal", "mutacion_velocidad", "mutacion_prioridad"
        self.color = self._obtener_color()
        
        # Velocidad: mutación de velocidad mueve más casillas por tick, mismos pasos de vida
        self.velocidad = 2 if tipo_mutacion == "mutacion_velocidad" else 1
        self.pasos_vida = pasos_vida
        self.pasos_restantes = self.pasos_vida
        self.trayectoria = [(self.x, self.y)]
        self.activa = True
        self.en_casa = True
        self.veces_comido = 0
        self.ha_comido_hoy = False
        self.salio_de_casa = False
        self.debe_morir = False
        self.puede_reproducirse = False
    
    def _obtener_color(self):
        """Retorna el color según el tipo de mutación"""
        if self.tipo_mutacion == "mutacion_velocidad":
            return COLOR_MUTACION_VELOCIDAD
        elif self.tipo_mutacion == "mutacion_prioridad":
            return COLOR_MUTACION_PRIORIDAD
        else:
            return COLOR_NORMAL
        
    def esta_en_borde(self, limites):
        """Verifica si la partícula está en el borde (casa)"""
        return (self.x == limites['izq'] or self.x == limites['der'] or
                self.y == limites['arr'] or self.y == limites['abaj'])
    
    def mover(self, limites):
        """Mueve la partícula; la mutación de velocidad realiza más pasos por tick"""
        if self.pasos_restantes <= 0 or not self.activa:
            return False

        direcciones = [
            (TAMANO_PASO, 0),      # Derecha
            (-TAMANO_PASO, 0),     # Izquierda
            (0, TAMANO_PASO),      # Abajo
            (0, -TAMANO_PASO)      # Arriba
        ]

        movio = False
        # Mutación velocidad: realiza varios subpasos en el mismo tick
        for _ in range(self.velocidad):
            if self.pasos_restantes <= 0 or not self.activa:
                break

            dx, dy = random.choice(direcciones)
            nuevo_x = max(limites['izq'], min(self.x + dx, limites['der']))
            nuevo_y = max(limites['arr'], min(self.y + dy, limites['abaj']))

            self.x = nuevo_x
            self.y = nuevo_y
            self.trayectoria.append((self.x, self.y))
            self.pasos_restantes -= 1
            movio = True

            # Verificar si está en casa
            if self.esta_en_borde(limites):
                self.en_casa = True
            else:
                self.en_casa = False
                if not self.salio_de_casa:
                    self.salio_de_casa = True

        return movio
    
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
    
    def obtener_tipo_hijo(self):
        """Determina el tipo de mutación del hijo basado en veces_comido del padre"""
        if self.veces_comido >= 3:
            # Mutación: 50% Mutación 1 (velocidad) o Mutación 2 (prioridad)
            return random.choice(["mutacion_velocidad", "mutacion_prioridad"])
        else:
            # Sin mutación: mismo tipo que el padre
            return self.tipo_mutacion
    
    def obtener_tipo_heredado(self):
        """Si es mutado, retorna tipo heredado con 75% misma mutación, 25% normal"""
        if self.tipo_mutacion in ["mutacion_velocidad", "mutacion_prioridad"]:
            # 75% misma mutación, 25% normal
            if random.random() < 0.75:
                return self.tipo_mutacion
            else:
                return "normal"
        return self.tipo_mutacion
        
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
        particula = Particula(x, y, pasos_vida, tipo_mutacion="normal")
        particulas.append(particula)
    return particulas


def dibujar_paredes(pantalla, limites):
    """Dibuja las paredes del ambiente"""
    ancho = limites['der'] - limites['izq']
    alto = limites['abaj'] - limites['arr']
    pygame.draw.rect(pantalla, BLANCO, (limites['izq'], limites['arr'], ancho, alto), 3)
    
    # Resaltar que el borde es la casa
    pygame.draw.rect(pantalla, VERDE, (limites['izq'], limites['arr'], ancho, alto), 1)


def intentar_comer_con_prioridad(particulas, posicion_comida):
    """
    Maneja el sistema de prioridad de comida cuando múltiples partículas llegan a la misma comida.
    Reglas:
    - Mutación 2 (verde) tiene prioridad sobre normal (blanco) y mutación 1 (rojo)
    - Si hay múltiples verdes, 50-50 entre ellos
    - Si hay múltiples del mismo tipo, 50-50 entre ellos
    """
    particulas_en_comida = [p for p in particulas if p.x == posicion_comida[0] and p.y == posicion_comida[1] and p.activa and not p.en_casa]
    
    if not particulas_en_comida:
        return None
    
    # Separar por tipo
    verdes = [p for p in particulas_en_comida if p.tipo_mutacion == "mutacion_prioridad"]
    rojos = [p for p in particulas_en_comida if p.tipo_mutacion == "mutacion_velocidad"]
    blancos = [p for p in particulas_en_comida if p.tipo_mutacion == "normal"]
    
    # Prioridad: Verdes > Rojos > Blancos
    if verdes:
        return random.choice(verdes)
    elif rojos:
        return random.choice(rojos)
    elif blancos:
        return random.choice(blancos)
    
    return None


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

    campo_dias = CampoTexto((ANCHO_VENTANA//2 + 140, 220, 120, 45), str(NUM_DIAS))
    campo_duracion = CampoTexto((ANCHO_VENTANA//2 + 140, 290, 120, 45), str(DURACION_DIA))
    campo_particulas = CampoTexto((ANCHO_VENTANA//2 + 140, 360, 120, 45), "50")
    campo_comida = CampoTexto((ANCHO_VENTANA//2 + 140, 430, 120, 45), str(PORCENTAJE_COMIDA))
    campo_pasos = CampoTexto((ANCHO_VENTANA//2 + 140, 500, 120, 45), str(PASOS_POR_VIDA))

    boton_iniciar = Boton((ANCHO_VENTANA//2 - 160, 620, 150, 60), "INICIAR", VERDE, (102, 187, 106))
    boton_salir = Boton((ANCHO_VENTANA//2 + 20, 620, 150, 60), "SALIR", ROJO, (200, 50, 50))

    corriendo = True
    error_msg = ""
    while corriendo:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            campo_dias.manejar_evento(evento)
            campo_duracion.manejar_evento(evento)
            campo_particulas.manejar_evento(evento)
            campo_comida.manejar_evento(evento)
            campo_pasos.manejar_evento(evento)

            if evento.type == pygame.MOUSEBUTTONDOWN:
                if boton_iniciar.click(evento.pos):
                    error_msg = ""
                    pasos_val = campo_pasos.valor(minimo=1, maximo=500, defecto=PASOS_POR_VIDA)
                    duracion_val = campo_duracion.valor(minimo=1, maximo=5000, defecto=DURACION_DIA)
                    if duracion_val <= pasos_val:
                        error_msg = "La duración del día debe ser mayor que los pasos por vida."
                    else:
                        return {
                            "dias": campo_dias.valor(minimo=1, maximo=999, defecto=NUM_DIAS),
                            "duracion": duracion_val,
                            "particulas": campo_particulas.valor(minimo=1, maximo=2000, defecto=50),
                            "comida": campo_comida.valor(minimo=1, maximo=90, defecto=PORCENTAJE_COMIDA),
                            "pasos": pasos_val
                        }
                if boton_salir.click(evento.pos):
                    pygame.quit()
                    sys.exit()

        pantalla.fill(NEGRO)
        titulo = fuente_titulo.render("Configurar Simulación", True, AZUL_BOTON)
        pantalla.blit(titulo, titulo.get_rect(center=(ANCHO_VENTANA//2, 120)))

        labels = [
            "Número de días",
            "Duración del día (pasos)",
            "Partículas iniciales",
            "% de comida en mapa",
            "Pasos por vida",
        ]
        campos = [campo_dias, campo_duracion, campo_particulas, campo_comida, campo_pasos]
        y_base = 220
        for i, (lbl, campo) in enumerate(zip(labels, campos)):
            texto = fuente.render(lbl + ":", True, BLANCO)
            pantalla.blit(texto, (ANCHO_VENTANA//2 - 260, y_base + i*70))
            campo.dibujar(pantalla, fuente)

        if error_msg:
            error_txt = fuente_small.render(error_msg, True, ROJO)
            pantalla.blit(error_txt, (ANCHO_VENTANA//2 - error_txt.get_width()//2, 580))

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

    # Garantizar que la duración del día siempre sea mayor a los pasos de vida
    duracion_dia = max(duracion_dia, pasos_vida + 1)

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
        # Retornar: particulas, comida, historial_poblacion, historial_tipos, dia, paso, pausado, velocidad
        return part, food, [len(part)], [{"normal": len(part), "rojo": 0, "verde": 0}], 1, 0, False, slider_vel.valor

    particulas, comida_pos, historial_poblacion, historial_tipos, dia_actual, paso_actual_dia, pausado, velocidad = reset_state()
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
                    particulas, comida_pos, historial_poblacion, historial_tipos, dia_actual, paso_actual_dia, pausado, velocidad = reset_state()
                    anim_muertes.clear()
                if boton_menu.click(evento.pos):
                    return None, None

        velocidad = slider_vel.valor

        # Simulación del día
        if not pausado and paso_actual_dia < duracion_dia:
            for particula in particulas:
                if particula.activa and particula.pasos_restantes > 0:
                    particula.mover(limites)

                    # Regla 9: Intentar comer si hay comida
                    if not particula.en_casa:
                        if (particula.x, particula.y) in comida_pos:
                            # Usar sistema de prioridad de comida
                            ganador = intentar_comer_con_prioridad(particulas, (particula.x, particula.y))
                            if ganador == particula:
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
                        # Si comió 2 veces: hijo igual al padre
                        # Si comió 3+ veces: hijo puede mutar
                        tipo_hijo = particula.obtener_tipo_hijo()
                        
                        # Si el hijo es mutado, aplicar herencia (75% misma mutación, 25% normal)
                        if tipo_hijo in ["mutacion_velocidad", "mutacion_prioridad"]:
                            # El hijo nace con la mutación, luego aplicamos herencia
                            tipo_final = tipo_hijo
                            # Si el padre es mutado, el hijo puede perder la mutación
                            if particula.tipo_mutacion in ["mutacion_velocidad", "mutacion_prioridad"]:
                                if random.random() >= 0.75:  # 25% de perder mutación
                                    tipo_final = "normal"
                        else:
                            # Tipo normal
                            tipo_final = tipo_hijo
                        
                        x, y = generar_posicion_borde(limites)
                        hijo = Particula(x, y, pasos_vida, tipo_mutacion=tipo_final)
                        nuevas_particulas.append(hijo)
                else:
                    # Solo agregar animación si no murió durante el día (Regla 5)
                    if not particula.debe_morir:
                        anim_muertes.append({"pos": (particula.x, particula.y), "frames": 15})

            particulas = sobrevivientes + nuevas_particulas

            if len(particulas) == 0:
                historial_poblacion.append(0)
                historial_tipos.append({"normal": 0, "rojo": 0, "verde": 0})
                break

            for p in particulas:
                p.reiniciar_dia(limites)

            comida_pos = generar_comida(limites, porcentaje_comida)
            historial_poblacion.append(len(particulas))
            
            # Registrar cantidad de cada tipo de partícula
            num_normales = len([p for p in particulas if p.tipo_mutacion == "normal"])
            num_rojos = len([p for p in particulas if p.tipo_mutacion == "mutacion_velocidad"])
            num_verdes = len([p for p in particulas if p.tipo_mutacion == "mutacion_prioridad"])
            historial_tipos.append({"normal": num_normales, "rojo": num_rojos, "verde": num_verdes})
            
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
            f"Normales: {len([p for p in particulas if p.tipo_mutacion == 'normal'])}",
            f"Rojos: {len([p for p in particulas if p.tipo_mutacion == 'mutacion_velocidad'])}",
            f"Verdes: {len([p for p in particulas if p.tipo_mutacion == 'mutacion_prioridad'])}",
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

    return historial_poblacion, historial_tipos


def mostrar_grafica_poblacion(historial_poblacion):
    """Muestra una gráfica de la evolución de la población"""
    fig = plt.figure(figsize=(10, 6), facecolor='#1a1a1a')
    ax = fig.add_subplot(111)
    ax.set_facecolor('#2d2d2d')
    ax.plot(range(len(historial_poblacion)), historial_poblacion, marker='o', 
             linewidth=2, markersize=6, color='#42A5F5')
    ax.set_xlabel('Día', fontsize=12, color='white')
    ax.set_ylabel('Población', fontsize=12, color='white')
    ax.set_title('Evolución de la Población a lo Largo del Tiempo', fontsize=14, fontweight='bold', color='white')
    ax.grid(True, alpha=0.3, color='white')
    ax.tick_params(colors='white')
    plt.tight_layout()
    plt.show()


def pantalla_graficas(pantalla, reloj, historial_poblacion, historial_tipos):
    """Pantalla interactiva para mostrar las gráficas con botón para volver"""
    fuente_titulo = pygame.font.Font(None, 48)
    fuente = pygame.font.Font(None, 28)
    
    boton_volver = Boton((ANCHO_VENTANA//2 - 75, ALTO_VENTANA - 80, 150, 60), "VOLVER", AZUL_BOTON, (90, 190, 255))
    
    # Crear las figuras de matplotlib
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), facecolor='#1a1a1a')
    ax1.set_facecolor('#2d2d2d')
    ax2.set_facecolor('#2d2d2d')
    
    # Gráfica 1: Evolución total de la población
    ax1.plot(range(len(historial_poblacion)), historial_poblacion, marker='o', 
             linewidth=2, markersize=6, color='#42A5F5', label='Población Total')
    ax1.set_xlabel('Día', fontsize=12, color='white')
    ax1.set_ylabel('Población', fontsize=12, color='white')
    ax1.set_title('Evolución de la Población a lo Largo del Tiempo', fontsize=13, fontweight='bold', color='white')
    ax1.grid(True, alpha=0.3, color='white')
    ax1.tick_params(colors='white')
    ax1.legend(facecolor='#2d2d2d', edgecolor='white', labelcolor='white')
    
    # Gráfica 2: Desglose por tipo
    dias = range(len(historial_tipos))
    normales = [h["normal"] for h in historial_tipos]
    rojos = [h["rojo"] for h in historial_tipos]
    verdes = [h["verde"] for h in historial_tipos]
    
    ax2.plot(dias, normales, marker='o', linewidth=2, markersize=6, color='#FFD700', label='Normales (Dorado)')
    ax2.plot(dias, rojos, marker='s', linewidth=2, markersize=6, color='#FF0000', label='Mutación Velocidad (Rojo)')
    ax2.plot(dias, verdes, marker='^', linewidth=2, markersize=6, color='#00FF00', label='Mutación Prioridad (Verde)')
    ax2.set_xlabel('Día', fontsize=12, color='white')
    ax2.set_ylabel('Cantidad de Partículas', fontsize=12, color='white')
    ax2.set_title('Población por Tipo de Mutación', fontsize=13, fontweight='bold', color='white')
    ax2.grid(True, alpha=0.3, color='white')
    ax2.tick_params(colors='white')
    ax2.legend(facecolor='#2d2d2d', edgecolor='white', labelcolor='white')
    
    # Ajustar diseño
    plt.tight_layout()
    
    # Mostrar las gráficas
    plt.show()


def pantalla_fin_simulacion(pantalla, reloj, historial_poblacion, historial_tipos):
    """Pantalla final con botón para ver gráficas"""
    fuente_titulo = pygame.font.Font(None, 56)
    fuente_grande = pygame.font.Font(None, 40)
    fuente = pygame.font.Font(None, 28)
    
    boton_graficas = Boton((ANCHO_VENTANA//2 - 100, ALTO_VENTANA//2 + 50, 200, 70), "VER GRÁFICAS", VERDE, (102, 187, 106))
    boton_salir = Boton((ANCHO_VENTANA//2 - 100, ALTO_VENTANA//2 + 150, 200, 70), "SALIR", ROJO, (200, 50, 50))
    
    corriendo = True
    while corriendo:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if boton_graficas.click(evento.pos):
                    pantalla_graficas(pantalla, reloj, historial_poblacion, historial_tipos)
                if boton_salir.click(evento.pos):
                    pygame.quit()
                    
                    # Mostrar resumen en consola
                    print("\n=== RESULTADOS DE LA SIMULACIÓN ===")
                    print(f"Población inicial: {historial_poblacion[0]}")
                    print(f"Población final: {historial_poblacion[-1]}")
                    print(f"Población máxima: {max(historial_poblacion)}")
                    print(f"Población mínima: {min(historial_poblacion)}")
                    print("=\n")
                    
                    sys.exit()
        
        pantalla.fill(NEGRO)
        
        # Título
        titulo = fuente_titulo.render("Simulación Completada", True, CYAN)
        pantalla.blit(titulo, titulo.get_rect(center=(ANCHO_VENTANA//2, 80)))
        
        # Estadísticas finales
        y_stats = 200
        stats_lines = [
            f"Población inicial: {historial_poblacion[0]}",
            f"Población final: {historial_poblacion[-1]}",
            f"Población máxima: {max(historial_poblacion)}",
            f"Población mínima: {min(historial_poblacion)}"
        ]
        
        for i, linea in enumerate(stats_lines):
            texto = fuente_grande.render(linea, True, BLANCO)
            pantalla.blit(texto, (ANCHO_VENTANA//2 - texto.get_width()//2, y_stats + i*50))
        
        # Instrucciones
        instruccion = fuente.render("Presiona el botón para ver las gráficas o salir", True, GRIS)
        pantalla.blit(instruccion, instruccion.get_rect(center=(ANCHO_VENTANA//2, ALTO_VENTANA//2 - 20)))
        
        boton_graficas.dibujar(pantalla, fuente_grande)
        boton_salir.dibujar(pantalla, fuente_grande)
        
        pygame.display.flip()
        reloj.tick(60)


def main():
    """Función principal"""
    pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
    pygame.display.set_caption("Simulación de Selección Natural")
    reloj = pygame.time.Clock()

    while True:
        config = pantalla_configuracion(pantalla, reloj)

        # Ejecutar simulación
        resultado = simulacion(
            pantalla,
            reloj,
            config["dias"],
            config["pasos"],
            config["duracion"],
            config["comida"],
            config["particulas"],
        )
        
        # Si resultado es (None, None), el usuario quiere volver al menú
        if resultado == (None, None):
            continue
        
        # Si llegamos aquí, la simulación terminó naturalmente
        historial_poblacion, historial_tipos = resultado
        
        # Mostrar pantalla final con opciones
        pantalla_fin_simulacion(pantalla, reloj, historial_poblacion, historial_tipos)
        break


if __name__ == "__main__":
    main()
