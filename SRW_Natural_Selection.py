import pygame
import random
import sys
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FuncFormatter

# Inicializar Pygame
pygame.init()

#  PARÁMETROS CONFIGURABLES DE LA SIMULACIÓN 
ANCHO_VENTANA = 1000
ALTO_VENTANA = 750
MARGEN = 50
TAMANO_PASO = 20  # Tamaño de cada paso en píxeles
PASOS_POR_VIDA = 100  # Número de pasos que puede dar cada partícula
DURACION_DIA = 300  # Pasos del día (>PASOS_POR_VIDA)
PORCENTAJE_COMIDA = 20  # Porcentaje del mapa con comida (valor por defecto)
NUM_DIAS = 30  # Número de días a simular (valor por defecto)
TAMANO_CELDA = 20  

# Parámetros de DEPREDADORES
NUM_DEPREDADORES = 5  # Número de depredadores que aparecen en día de purga
FRECUENCIA_PURGA = 3  # Cada cuántos días aparecen los depredadores
RADIO_VISION_DEPREDADOR = 5 * 20  # 5 pasos de visión para depredadores (100 píxeles)
RADIO_VISION_PRESA = 3 * 20  # 3 pasos de visión para presas (60 píxeles)
VELOCIDAD_DEPREDADOR = 2 

# Parámetros de STAMINA
STAMINA_MAXIMA = 100 
STAMINA_RECARGA_POR_COMIDA = 60  
STAMINA_AGOTAMIENTO = 1.0  # Stamina perdido por paso sin comer

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
COLOR_MUTACION_VELOCIDAD = (0, 255, 0)  # Verde - Velocidad aumentada
COLOR_MUTACION_PRIORIDAD = (255, 0, 0)  # Rojo - Prioridad para comer
COLOR_DEPREDADOR = (139, 0, 139)  # Morado oscuro - Depredador


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
        self.velocidad_base = 2 if tipo_mutacion == "mutacion_velocidad" else 1
        self.velocidad = self.velocidad_base  # Velocidad ajustada por stamina
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
        
        # Sistema de STAMINA
        self.stamina = STAMINA_MAXIMA
        self.stamina_anterior = STAMINA_MAXIMA
        
        # Sistema de VIDA
        self.vida_maxima = 2 if tipo_mutacion == "mutacion_prioridad" else 1
        self.vida_actual = self.vida_maxima
        self.invulnerable_frames = 0  # Frames de invulnerabilidad tras recibir daño
        self.huyendo = False  # Estado de huida
    
    def _obtener_color(self):
        """Retorna el color según el tipo de mutación"""
        if self.tipo_mutacion == "mutacion_velocidad":
            return COLOR_MUTACION_VELOCIDAD
        elif self.tipo_mutacion == "mutacion_prioridad":
            return COLOR_MUTACION_PRIORIDAD
        else:
            return COLOR_NORMAL
    
    def actualizar_velocidad_por_stamina(self):
        """Ajusta la velocidad según el stamina actual"""
        # Proporción de stamina (0 a 1)
        proporcion_stamina = max(0, min(1, self.stamina / STAMINA_MAXIMA))
        # La velocidad varía de 0% a 100% de la velocidad base según el stamina
        self.velocidad = max(1, int(self.velocidad_base * proporcion_stamina))
        if self.velocidad == 0:
            self.velocidad = 1  # Mínimo 1 para poder moverse
    
    def recargar_stamina(self):
        """Recarga el stamina al comer"""
        self.stamina = min(STAMINA_MAXIMA, self.stamina + STAMINA_RECARGA_POR_COMIDA)
    
    def agotar_stamina(self, cantidad=STAMINA_AGOTAMIENTO):
        """Reduce el stamina por no comer"""
        self.stamina = max(0, self.stamina - cantidad)
        self.actualizar_velocidad_por_stamina()
    
    def recibir_dano(self):
        """Recibe daño de un depredador"""
        if self.invulnerable_frames > 0:
            return False  # Aún invulnerable
        
        self.vida_actual -= 1
        self.invulnerable_frames = 30  # 30 frames de invulnerabilidad (~0.5 segundos a 60 FPS)
        
        if self.vida_actual <= 0:
            self.activa = False
            self.debe_morir = True
            return True  # Murió
        return False  # Sobrevivió
    
    def actualizar_invulnerabilidad(self):
        """Actualiza el contador de invulnerabilidad"""
        if self.invulnerable_frames > 0:
            self.invulnerable_frames -= 1
    
    def detectar_depredador_cercano(self, depredadores):
        """Detecta si hay un depredador en el radio de visión (3 pasos)"""
        for depredador in depredadores:
            if not depredador.activo:
                continue
            # Calcular distancia Manhattan (solo direcciones cardinales)
            distancia_manhattan = abs(self.x - depredador.x) + abs(self.y - depredador.y)
            if distancia_manhattan <= RADIO_VISION_PRESA:
                return depredador
        return None
    
    def calcular_vector_huida(self, depredador):
        """Calcula dirección opuesta al depredador (solo direcciones cardinales)"""
        dx = self.x - depredador.x
        dy = self.y - depredador.y
        
        # Elegir la dirección cardinal que maximiza la distancia
        # Priorizar el eje con mayor diferencia
        if abs(dx) > abs(dy):
            # Moverse horizontalmente
            if dx > 0:
                return TAMANO_PASO, 0  # Derecha (alejarse)
            else:
                return -TAMANO_PASO, 0  # Izquierda (alejarse)
        else:
            # Moverse verticalmente
            if dy > 0:
                return 0, TAMANO_PASO  # Abajo (alejarse)
            else:
                return 0, -TAMANO_PASO  # Arriba (alejarse)
        
    def esta_en_borde(self, limites):
        """Verifica si la partícula está en el borde (casa)"""
        return (self.x == limites['izq'] or self.x == limites['der'] or
                self.y == limites['arr'] or self.y == limites['abaj'])
    
    def mover(self, limites, depredadores=None):
        """Mueve la partícula; la mutación de velocidad realiza más pasos por tick"""
        if self.pasos_restantes <= 0 or not self.activa:
            return False

        # Actualizar invulnerabilidad
        self.actualizar_invulnerabilidad()
        
        # Detectar depredadores cercanos
        depredador_cercano = None
        if depredadores:
            depredador_cercano = self.detectar_depredador_cercano(depredadores)
        
        self.huyendo = depredador_cercano is not None
        
        direcciones = [
            (TAMANO_PASO, 0),      # Derecha
            (-TAMANO_PASO, 0),     # Izquierda
            (0, TAMANO_PASO),      # Abajo
            (0, -TAMANO_PASO)      # Arriba
        ]

        movio = False
        # Actualizar velocidad según stamina actual
        self.actualizar_velocidad_por_stamina()
        
        # Mutación velocidad: realiza varios subpasos en el mismo tick
        # Velocidad ajustada por stamina
        for _ in range(self.velocidad):
            if self.pasos_restantes <= 0 or not self.activa:
                break

            # Si hay un depredador cercano, huir
            if self.huyendo and depredador_cercano:
                dx, dy = self.calcular_vector_huida(depredador_cercano)
            else:
                dx, dy = random.choice(direcciones)
            
            nuevo_x = max(limites['izq'], min(self.x + dx, limites['der']))
            nuevo_y = max(limites['arr'], min(self.y + dy, limites['abaj']))

            # Alinear al grid
            nuevo_x = (nuevo_x // TAMANO_PASO) * TAMANO_PASO
            nuevo_y = (nuevo_y // TAMANO_PASO) * TAMANO_PASO

            self.x = nuevo_x
            self.y = nuevo_y
            self.trayectoria.append((self.x, self.y))
            self.pasos_restantes -= 1
            
            # Agotar stamina por cada paso realizado
            if not self.en_casa:
                self.agotar_stamina()
            
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
            self.recargar_stamina()  # Recargar stamina al comer
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
        # Reiniciar stamina al máximo
        self.stamina = STAMINA_MAXIMA
        self.actualizar_velocidad_por_stamina()
        # Reiniciar vida al máximo
        self.vida_actual = self.vida_maxima
        self.invulnerable_frames = 0
        self.huyendo = False
    
    def obtener_tipo_hijo(self):
        """Determina el tipo de mutación del hijo basado en veces_comido del padre"""
        if self.veces_comido >= 3:
            # Mutación: 50% Mutación 1 (velocidad) o Mutación 2 (prioridad)
            return random.choice(["mutacion_velocidad", "mutacion_prioridad"])
        else:
            # Sin mutación: mismo tipo que el padre
            return self.tipo_mutacion
    
    def obtener_tipo_heredado(self):
        """Si es mutado, retorna tipo heredado con 80% misma mutación, 20% normal"""
        if self.tipo_mutacion in ["mutacion_velocidad", "mutacion_prioridad"]:
            # 80% misma mutación, 20% normal
            if random.random() < 0.8:
                return self.tipo_mutacion
            else:
                return "normal"
        return self.tipo_mutacion
        
    def dibujar(self, pantalla, mostrar_trayectoria=False):
        """Dibuja la partícula"""
        if mostrar_trayectoria and len(self.trayectoria) > 1:
            pygame.draw.lines(pantalla, self.color, False, self.trayectoria, 1)
        
        # Dibujar la partícula
        pygame.draw.circle(pantalla, self.color, (self.x, self.y), 7)
        
        # Si está huyendo, dibujar indicador
        if self.huyendo:
            pygame.draw.circle(pantalla, NARANJA, (self.x, self.y), 10, 1)
        
        # Si está en casa, dibujar un círculo alrededor
        if self.en_casa:
            pygame.draw.circle(pantalla, VERDE, (self.x, self.y), 11, 2)


# Clase Depredador
class Depredador:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.activo = True
        self.velocidad = VELOCIDAD_DEPREDADOR
        self.trayectoria = [(self.x, self.y)]
        self.particulas_eliminadas = 0
        self.objetivo = None  # Partícula objetivo actual
    
    def buscar_objetivo_cercano(self, particulas):
        """Busca la partícula más cercana dentro del rango de visión (5 pasos)"""
        particulas_activas = [p for p in particulas if p.activa and not p.en_casa]
        if not particulas_activas:
            return None
        
        # Encontrar la partícula más cercana dentro del rango de visión
        min_dist = float('inf')
        objetivo = None
        for p in particulas_activas:
            # Usar distancia Manhattan (solo direcciones cardinales)
            dist_manhattan = abs(self.x - p.x) + abs(self.y - p.y)
            if dist_manhattan <= RADIO_VISION_DEPREDADOR and dist_manhattan < min_dist:
                min_dist = dist_manhattan
                objetivo = p
        
        return objetivo
    
    def mover(self, limites, particulas):
        """Mueve el depredador: random walk por defecto, persigue si detecta presa en rango de 5 pasos"""
        if not self.activo:
            return False
        
        # Buscar objetivo en el rango de visión
        self.objetivo = self.buscar_objetivo_cercano(particulas)
        
        # Si no hay objetivo en rango, hacer simple random walk
        if not self.objetivo:
            direcciones = [
                (TAMANO_PASO, 0),      # Derecha
                (-TAMANO_PASO, 0),     # Izquierda
                (0, TAMANO_PASO),      # Abajo
                (0, -TAMANO_PASO)      # Arriba
            ]
            dx, dy = random.choice(direcciones)
        else:
            # Perseguir objetivo - elegir dirección cardinal que acerca más al objetivo
            dx_diff = self.objetivo.x - self.x
            dy_diff = self.objetivo.y - self.y
            
            # Elegir la dirección cardinal que más acerca al objetivo
            # Priorizar el eje con mayor diferencia
            if abs(dx_diff) > abs(dy_diff):
                # Moverse horizontalmente
                if dx_diff > 0:
                    dx, dy = TAMANO_PASO * self.velocidad, 0  # Derecha
                else:
                    dx, dy = -TAMANO_PASO * self.velocidad, 0  # Izquierda
            else:
                # Moverse verticalmente
                if dy_diff > 0:
                    dx, dy = 0, TAMANO_PASO * self.velocidad  # Abajo
                else:
                    dx, dy = 0, -TAMANO_PASO * self.velocidad  # Arriba
        
        nuevo_x = max(limites['izq'], min(self.x + dx, limites['der']))
        nuevo_y = max(limites['arr'], min(self.y + dy, limites['abaj']))
        
        self.x = nuevo_x
        self.y = nuevo_y
        self.trayectoria.append((self.x, self.y))
        
        return True
    
    def verificar_colision(self, particulas, anim_muertes):
        """Verifica colisión con partículas y aplica daño"""
        for particula in particulas:
            if not particula.activa or particula.en_casa:
                continue
            
            # Calcular distancia
            distancia = ((self.x - particula.x)**2 + (self.y - particula.y)**2)**0.5
            
            # Si están lo suficientemente cerca (radio de colisión)
            if distancia < 15:  # Radio de colisión
                murio = particula.recibir_dano()
                if murio:
                    self.particulas_eliminadas += 1
                    anim_muertes.append({"pos": (particula.x, particula.y), "frames": 15})
                    # Buscar nuevo objetivo
                    self.objetivo = None
    
    def dibujar(self, pantalla, mostrar_trayectoria=True):
        """Dibuja el depredador como círculo morado con su trayectoria"""
        if not self.activo:
            return
        
        # Dibujar trayectoria del depredador
        if mostrar_trayectoria and len(self.trayectoria) > 1:
            pygame.draw.lines(pantalla, COLOR_DEPREDADOR, False, self.trayectoria, 2)
        
        # Dibujar depredador como círculo morado sólido
        pygame.draw.circle(pantalla, COLOR_DEPREDADOR, (self.x, self.y), 10)
        pygame.draw.circle(pantalla, BLANCO, (self.x, self.y), 10, 2)


# Funciones auxiliares
def generar_posicion_borde(limites):
    """Genera una posición aleatoria en el borde (casa) y retorna con el primer movimiento hacia adentro"""
    borde = random.choice(['izq', 'der', 'arr', 'abaj'])
    
    if borde == 'izq':
        x = limites['izq'] + TAMANO_PASO  # Primer paso hacia adentro
        y = (random.randrange(limites['arr'], limites['abaj'] + 1, TAMANO_PASO) // TAMANO_PASO) * TAMANO_PASO
    elif borde == 'der':
        x = limites['der'] - TAMANO_PASO  # Primer paso hacia adentro
        y = (random.randrange(limites['arr'], limites['abaj'] + 1, TAMANO_PASO) // TAMANO_PASO) * TAMANO_PASO
    elif borde == 'arr':
        x = (random.randrange(limites['izq'], limites['der'] + 1, TAMANO_PASO) // TAMANO_PASO) * TAMANO_PASO
        y = limites['arr'] + TAMANO_PASO  # Primer paso hacia adentro
    else:  # 'abaj'
        x = (random.randrange(limites['izq'], limites['der'] + 1, TAMANO_PASO) // TAMANO_PASO) * TAMANO_PASO
        y = limites['abaj'] - TAMANO_PASO  # Primer paso hacia adentro
    
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
    - Mutación Rojo (prioridad) tiene prioridad máxima
    - Mutación Verde (velocidad) tiene prioridad media
    - Normal (blanco) tiene prioridad mínima
    - Si hay múltiples del mismo tipo, 50-50 entre ellos
    """
    # Buscar partículas activas en la posición de comida (sin filtrar por en_casa)
    particulas_en_comida = [p for p in particulas if p.x == posicion_comida[0] and p.y == posicion_comida[1] and p.activa]
    
    if not particulas_en_comida:
        return None
    
    # Separar por tipo
    rojos = [p for p in particulas_en_comida if p.tipo_mutacion == "mutacion_prioridad"]
    verdes = [p for p in particulas_en_comida if p.tipo_mutacion == "mutacion_velocidad"]
    blancos = [p for p in particulas_en_comida if p.tipo_mutacion == "normal"]
    
    # Prioridad: Rojo (Alta) > Verde (Media) > Blanco (Baja)
    if rojos:
        return random.choice(rojos)
    elif verdes:
        return random.choice(verdes)
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

    campo_dias = CampoTexto((ANCHO_VENTANA//2 + 140, 180, 120, 45), str(NUM_DIAS))
    campo_duracion = CampoTexto((ANCHO_VENTANA//2 + 140, 240, 120, 45), str(DURACION_DIA))
    campo_particulas = CampoTexto((ANCHO_VENTANA//2 + 140, 300, 120, 45), "50")
    campo_comida = CampoTexto((ANCHO_VENTANA//2 + 140, 360, 120, 45), str(PORCENTAJE_COMIDA))
    campo_pasos = CampoTexto((ANCHO_VENTANA//2 + 140, 420, 120, 45), str(PASOS_POR_VIDA))
    campo_depredadores = CampoTexto((ANCHO_VENTANA//2 + 140, 480, 120, 45), str(NUM_DEPREDADORES))
    campo_frecuencia = CampoTexto((ANCHO_VENTANA//2 + 140, 540, 120, 45), str(FRECUENCIA_PURGA))

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
            campo_depredadores.manejar_evento(evento)
            campo_frecuencia.manejar_evento(evento)

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
                            "pasos": pasos_val,
                            "depredadores": campo_depredadores.valor(minimo=0, maximo=50, defecto=NUM_DEPREDADORES),
                            "frecuencia_purga": campo_frecuencia.valor(minimo=0, maximo=100, defecto=FRECUENCIA_PURGA)
                        }
                if boton_salir.click(evento.pos):
                    pygame.quit()
                    sys.exit()

        pantalla.fill(NEGRO)
        titulo = fuente_titulo.render("Configuración", True, AZUL_BOTON)
        pantalla.blit(titulo, titulo.get_rect(center=(ANCHO_VENTANA//2, 120)))

        labels = [
            "Número de días",
            "Duración del día (pasos)",
            "Partículas iniciales",
            "Comida en el mapa (%)",
            "Pasos por vida",
            "Depredadores por purga",
            "Frecuencia de purga",
        ]
        campos = [campo_dias, campo_duracion, campo_particulas, campo_comida, campo_pasos, campo_depredadores, campo_frecuencia]
        y_base = 180
        for i, (lbl, campo) in enumerate(zip(labels, campos)):
            texto = fuente.render(lbl + ":", True, BLANCO)
            pantalla.blit(texto, (ANCHO_VENTANA//2 - 300, y_base + i*60))
            campo.dibujar(pantalla, fuente)

        if error_msg:
            error_txt = fuente_small.render(error_msg, True, ROJO)
            pantalla.blit(error_txt, (ANCHO_VENTANA//2 - error_txt.get_width()//2, 580))

        boton_iniciar.dibujar(pantalla, fuente)
        boton_salir.dibujar(pantalla, fuente)

        pygame.display.flip()
        reloj.tick(60)


def simulacion(pantalla, reloj, num_dias, pasos_vida, duracion_dia, porcentaje_comida, num_particulas_inicial, num_depredadores=5, frecuencia_purga=3):
    """Ejecuta la simulación de selección natural por varios días con sistema de depredadores"""
    fuente_grande = pygame.font.Font(None, 40)
    fuente = pygame.font.Font(None, 28)
    fuente_pequena = pygame.font.Font(None, 22)

    # Garantizar que la duración del día siempre sea mayor a los pasos de vida
    duracion_dia = max(duracion_dia, pasos_vida + 1)

    # Definir límites del mundo (alineados al grid)
    limites = {
        'izq': (MARGEN // TAMANO_PASO) * TAMANO_PASO,
        'der': ((ANCHO_VENTANA - MARGEN - 300) // TAMANO_PASO) * TAMANO_PASO,
        'arr': ((MARGEN + 100) // TAMANO_PASO) * TAMANO_PASO,
        'abaj': ((ALTO_VENTANA - MARGEN) // TAMANO_PASO) * TAMANO_PASO
    }

    # Botones y slider
    boton_pausa = Boton((ANCHO_VENTANA - 275, 20, 85, 45), "PAUSA", AZUL_BOTON, (90, 190, 255))
    boton_reiniciar = Boton((ANCHO_VENTANA - 180, 20, 90, 45), "RESET", NARANJA, (255, 140, 60))
    boton_menu = Boton((ANCHO_VENTANA - 80, 20, 70, 45), "MENU", ROJO, (200, 50, 50))
    slider_vel = Slider(ANCHO_VENTANA - 260, 72, 210, 5, 120, 30)

    def reset_state():
        part = crear_particulas_iniciales(limites, num_particulas_inicial, pasos_vida)
        food = generar_comida(limites, porcentaje_comida)
        # Historial de depredadores: {dia, num_depredadores, particulas_eliminadas}
        hist_depredadores = []
        historial_estadisticas = []
        # Retornar: particulas, comida, historial_poblacion, historial_tipos, historial_depredadores, historial_estadisticas, dia, paso, pausado, velocidad
        return part, food, [len(part)], [{"normal": len(part), "verde": 0, "rojo": 0}], hist_depredadores, historial_estadisticas, 1, 0, False, slider_vel.valor

    particulas, comida_pos, historial_poblacion, historial_tipos, historial_depredadores, historial_estadisticas, dia_actual, paso_actual_dia, pausado, velocidad = reset_state()
    comida_inicial_dia = len(comida_pos)
    mostrar_trayectorias = False
    anim_muertes = []  # lista de {'pos': (x,y), 'frames': n}
    depredadores = []  # Lista de depredadores activos
    es_dia_purga = False

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
                    particulas, comida_pos, historial_poblacion, historial_tipos, historial_depredadores, dia_actual, paso_actual_dia, pausado, velocidad = reset_state()
                    anim_muertes.clear()
                    depredadores.clear()
                    es_dia_purga = False
                if boton_menu.click(evento.pos):
                    return None, None, None, None

        velocidad = slider_vel.valor

        # Simulación del día
        if not pausado and paso_actual_dia < duracion_dia:
            # Verificar si es día de purga y spawner depredadores
            if paso_actual_dia == 0 and frecuencia_purga > 0 and dia_actual % frecuencia_purga == 0:
                es_dia_purga = True
                depredadores.clear()
                for _ in range(num_depredadores):
                    x, y = generar_posicion_borde(limites)
                    depredador = Depredador(x, y)
                    depredadores.append(depredador)
            # Registrar comida inicial del día al primer paso
            if paso_actual_dia == 0:
                comida_inicial_dia = len(comida_pos)
            
            # Paso 1: Mover todas las partículas (con evasión de depredadores)
            for particula in particulas:
                if particula.activa and particula.pasos_restantes > 0:
                    particula.mover(limites, depredadores if es_dia_purga else None)
            
            # Paso 1.5: Mover depredadores y verificar colisiones
            if es_dia_purga:
                for depredador in depredadores:
                    depredador.mover(limites, particulas)
                    depredador.verificar_colision(particulas, anim_muertes)
            
            # Paso 2: Procesar comida SOLO para partículas activas que están fuera de casa
            # Se construye un mapeo de posición -> lista de partículas
            pos_a_particulas = {}
            for pos_comida in comida_pos:
                pos_a_particulas[pos_comida] = []
            
            for particula in particulas:
                if particula.activa and (particula.x, particula.y) in pos_a_particulas:
                    pos_a_particulas[(particula.x, particula.y)].append(particula)
            
            # Ahora procesar la comida - una partícula por posición de comida
            comidas_consumidas = set()
            for pos_comida, particulas_en_pos in pos_a_particulas.items():
                if particulas_en_pos:  # Si hay partículas en esta posición
                    # Aplicar reglas de prioridad
                    verdes = [p for p in particulas_en_pos if p.tipo_mutacion == "mutacion_prioridad"]
                    rojos = [p for p in particulas_en_pos if p.tipo_mutacion == "mutacion_velocidad"]
                    blancos = [p for p in particulas_en_pos if p.tipo_mutacion == "normal"]
                    
                    # Elegir ganador según prioridad
                    if verdes:
                        ganador = random.choice(verdes)
                    elif rojos:
                        ganador = random.choice(rojos)
                    else:
                        ganador = random.choice(blancos)
                    
                    # El ganador come
                    ganador.veces_comido += 1
                    ganador.ha_comido_hoy = True
                    ganador.recargar_stamina()
                    comidas_consumidas.add(pos_comida)
            
            # Eliminar comida consumida del mapa
            comida_pos -= comidas_consumidas
            
            # Paso 3: Manejar muertes por agotamiento y reglas de regreso a casa
            for particula in particulas:
                # Regla 5: Si salió de casa y se quedó sin pasos fuera de casa, muere INMEDIATAMENTE
                if particula.salio_de_casa and not particula.en_casa and particula.pasos_restantes <= 0 and particula.activa:
                    particula.activa = False
                    particula.debe_morir = True
                    anim_muertes.append({"pos": (particula.x, particula.y), "frames": 15})
                
                # Regla 19: Si regresó a casa y comió, se queda
                # Regla 10: Si regresó sin comer pero con pasos, debe salir de nuevo
                elif particula.en_casa and particula.salio_de_casa and particula.activa:
                    if particula.ha_comido_hoy:
                        # Regla 19: Se queda en casa
                        particula.activa = False
                        if particula.veces_comido >= 2:
                            particula.puede_reproducirse = True
                    elif particula.pasos_restantes > 0:
                        # Regla 10: Debe salir de nuevo
                        particula.en_casa = False

            paso_actual_dia += 1

        # Fin de día
        if paso_actual_dia >= duracion_dia and not pausado:
            # Registrar estadísticas del día
            historial_estadisticas.append({
                "dia": dia_actual,
                "poblacion_total": len(particulas),
                "comida": comida_inicial_dia,
                "vivas": len([p for p in particulas if p.activa]),
                "en_casa": len([p for p in particulas if p.en_casa]),
                "comieron": len([p for p in particulas if p.ha_comido_hoy]),
                "pueden_reproducirse": len([p for p in particulas if p.puede_reproducirse]),
                "normales": len([p for p in particulas if p.tipo_mutacion == "normal"]),
                "verdes": len([p for p in particulas if p.tipo_mutacion == "mutacion_velocidad"]),
                "rojos": len([p for p in particulas if p.tipo_mutacion == "mutacion_prioridad"]),
                "depredadores": len(depredadores) if es_dia_purga else 0
            })
            # Registrar estadísticas de depredadores si fue día de purga
            if es_dia_purga:
                vel_elim = sum(1 for p in particulas if not p.activa and p.debe_morir and p.tipo_mutacion == "mutacion_velocidad")
                pri_elim = sum(1 for p in particulas if not p.activa and p.debe_morir and p.tipo_mutacion == "mutacion_prioridad")
                nor_elim = sum(1 for p in particulas if not p.activa and p.debe_morir and p.tipo_mutacion == "normal")
                total_eliminadas = vel_elim + pri_elim + nor_elim
                
                historial_depredadores.append({
                    "dia": dia_actual,
                    "num_depredadores": len(depredadores),
                    "particulas_eliminadas": total_eliminadas,
                    "velocidad_eliminadas": vel_elim,
                    "prioridad_eliminadas": pri_elim,
                    "normal_eliminadas": nor_elim
                })
                # Eliminar depredadores al final del día
                depredadores.clear()
                es_dia_purga = False
            
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
                        
                        # Si el hijo es mutado, aplicar herencia (80% misma mutación, 20% normal)
                        if tipo_hijo in ["mutacion_velocidad", "mutacion_prioridad"]:
                            # El hijo nace con la mutación, luego aplicamos herencia
                            tipo_final = tipo_hijo
                            # Si el padre es mutado, el hijo puede perder la mutación
                            if particula.tipo_mutacion in ["mutacion_velocidad", "mutacion_prioridad"]:
                                if random.random() >= 0.8:  # 20% de perder mutación
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
                historial_tipos.append({"normal": 0, "verde": 0, "rojo": 0})
                break

            for p in particulas:
                p.reiniciar_dia(limites)

            comida_pos = generar_comida(limites, porcentaje_comida)
            comida_inicial_dia = len(comida_pos)
            historial_poblacion.append(len(particulas))
            
            # Registrar cantidad de cada tipo de partícula
            num_normales = len([p for p in particulas if p.tipo_mutacion == "normal"])
            num_verdes = len([p for p in particulas if p.tipo_mutacion == "mutacion_velocidad"])
            num_rojos = len([p for p in particulas if p.tipo_mutacion == "mutacion_prioridad"])
            historial_tipos.append({"normal": num_normales, "verde": num_verdes, "rojo": num_rojos})
            
            dia_actual += 1
            paso_actual_dia = 0

        # Dibujar
        pantalla.fill(NEGRO)

        pygame.draw.rect(pantalla, GRIS_OSCURO, (0, 0, ANCHO_VENTANA, 100))
        pygame.draw.line(pantalla, BLANCO, (0, 100), (ANCHO_VENTANA, 100), 2)

        titulo_dia = f"DÍA {dia_actual}/{num_dias}"
        if es_dia_purga:
            titulo_dia += " - PURGA"
        texto_dia = fuente_grande.render(titulo_dia, True, AZUL_BOTON if not es_dia_purga else ROJO)
        pantalla.blit(texto_dia, (20, 20))

        texto_poblacion = fuente.render(f"Población: {len(particulas)}", True, BLANCO)
        pantalla.blit(texto_poblacion, (320, 20))

        texto_comida = fuente.render(f"Comida: {len(comida_pos)}", True, BLANCO)
        pantalla.blit(texto_comida, (320, 60))

        if pausado:
            texto_pausa = fuente.render("PAUSADO", True, ROJO)
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

        # Dibujar depredadores con trayectoria
        for depredador in depredadores:
            depredador.dibujar(pantalla, mostrar_trayectorias)
        
        for particula in particulas:
            if particula.debe_morir:
                continue
            particula.dibujar(pantalla, mostrar_trayectorias)
            
            # Dibujar barra de stamina encima de la partícula
            if particula.activa:
                barra_x = particula.x - 10
                barra_y = particula.y - 18
                # Barra de fondo (gris oscuro)
                pygame.draw.rect(pantalla, GRIS_OSCURO, (barra_x, barra_y, 20, 6))
                # Barra de stamina (verde -> amarillo -> rojo según stamina)
                proporcion = particula.stamina / STAMINA_MAXIMA
                if proporcion > 0.5:
                    color_stamina = (0, 255 * (1 - proporcion), 255)  # Verde a cian
                elif proporcion > 0.25:
                    color_stamina = (255, 255 * proporcion, 0)  # Naranja a amarillo
                else:
                    color_stamina = (255, 0, 0)  # Rojo
                ancho_barra = max(1, int(20 * proporcion))
                pygame.draw.rect(pantalla, color_stamina, (barra_x, barra_y, ancho_barra, 6))

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
            "PARTÍCULAS",
            f"Normales: {len([p for p in particulas if p.tipo_mutacion == 'normal'])}",
            f"Verdes: {len([p for p in particulas if p.tipo_mutacion == 'mutacion_velocidad'])}",
            f"Rojos: {len([p for p in particulas if p.tipo_mutacion == 'mutacion_prioridad'])}",
            f"Depredadores: {len(depredadores)}",
            "",
            "CONTROLES",
            "ESPACIO / Botón: Pausa",
            "T: Trayectorias",
            "ESC: Salir"
        ]

        for i, linea in enumerate(lineas_panel):
            if i == 0 or i == 6 or i == 12:
                color = AZUL_BOTON
                fuente_usar = fuente
            else:
                color = BLANCO
                fuente_usar = fuente_pequena

            texto = fuente_usar.render(linea, True, color)
            pantalla.blit(texto, (panel_x + 10, y_pos + i * 28))

        pygame.display.flip()
        reloj.tick(velocidad)

    return historial_poblacion, historial_tipos, historial_depredadores, historial_estadisticas


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


def pantalla_graficas(pantalla, reloj, historial_poblacion, historial_tipos, historial_depredadores):
    """Pantalla interactiva para mostrar las gráficas con botón para volver"""
    fuente_titulo = pygame.font.Font(None, 48)
    fuente = pygame.font.Font(None, 28)
    
    boton_volver = Boton((ANCHO_VENTANA//2 - 75, ALTO_VENTANA - 80, 150, 60), "VOLVER", AZUL_BOTON, (90, 190, 255))
    
    # Crear las figuras de matplotlib
    fig = plt.figure(figsize=(16, 10), facecolor='#1a1a1a')
    ax1 = plt.subplot(2, 2, 1)
    ax2 = plt.subplot(2, 2, 2)
    ax3 = plt.subplot(2, 2, 3)
    ax4 = plt.subplot(2, 2, 4)
    
    ax1.set_facecolor('#2d2d2d')
    ax2.set_facecolor('#2d2d2d')
    ax3.set_facecolor('#2d2d2d')
    ax4.set_facecolor('#2d2d2d')
    
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
    ax2.plot(dias, verdes, marker='s', linewidth=2, markersize=6, color='#00FF00', label='Mutación Velocidad (Verde)')
    ax2.plot(dias, rojos, marker='^', linewidth=2, markersize=6, color='#FF0000', label='Mutación Prioridad (Rojo)')
    ax2.set_xlabel('Día', fontsize=12, color='white')
    ax2.set_ylabel('Cantidad de Partículas', fontsize=12, color='white')
    ax2.set_title('Población por Tipo de Mutación', fontsize=13, fontweight='bold', color='white')
    ax2.grid(True, alpha=0.3, color='white')
    ax2.tick_params(colors='white')
    ax2.legend(facecolor='#2d2d2d', edgecolor='white', labelcolor='white')
    
    # Gráfica 3: Partículas eliminadas por depredadores por día
    if historial_depredadores:
        dias_purga = [h["dia"] for h in historial_depredadores]
        eliminadas = [int(h["particulas_eliminadas"]) for h in historial_depredadores]
        
        ax3.bar(dias_purga, eliminadas, color='#8B008B', alpha=0.7, label='Partículas Eliminadas')
        ax3.set_xlabel('Día de Purga', fontsize=12, color='white')
        ax3.set_ylabel('Partículas Eliminadas', fontsize=12, color='white')
        ax3.set_title('Impacto de Depredadores por Día de Purga', fontsize=13, fontweight='bold', color='white')
        ax3.grid(True, alpha=0.3, color='white', axis='y')
        ax3.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax3.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x)}"))
        ax3.tick_params(colors='white')
        ax3.legend(facecolor='#2d2d2d', edgecolor='white', labelcolor='white')
    else:
        ax3.text(0.5, 0.5, 'No hubo días de purga', ha='center', va='center', 
                fontsize=14, color='white', transform=ax3.transAxes)
        ax3.set_title('Impacto de Depredadores', fontsize=13, fontweight='bold', color='white')
    
    # Gráfica 4: Desglose de tipos eliminados por depredadores
    if historial_depredadores:
        dias_purga = [h["dia"] for h in historial_depredadores]
        vel_elim = [int(h.get("velocidad_eliminadas", 0)) for h in historial_depredadores]
        pri_elim = [int(h.get("prioridad_eliminadas", 0)) for h in historial_depredadores]
        nor_elim = [int(h.get("normal_eliminadas", 0)) for h in historial_depredadores]
        
        width = 0.25
        x = range(len(dias_purga))
        
        ax4.bar([i - width for i in x], nor_elim, width, label='Normales', color='#FFD700', alpha=0.7)
        ax4.bar(x, vel_elim, width, label='Velocidad', color='#00FF00', alpha=0.7)
        ax4.bar([i + width for i in x], pri_elim, width, label='Prioridad', color='#FF0000', alpha=0.7)
        
        ax4.set_xlabel('Día de Purga', fontsize=12, color='white')
        ax4.set_ylabel('Cantidad Eliminada', fontsize=12, color='white')
        ax4.set_title('Tipos de Partículas Eliminadas por Depredadores', fontsize=13, fontweight='bold', color='white')
        ax4.set_xticks(x)
        ax4.set_xticklabels(dias_purga)
        ax4.grid(True, alpha=0.3, color='white', axis='y')
        ax4.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax4.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{int(x)}"))
        ax4.tick_params(colors='white')
        ax4.legend(facecolor='#2d2d2d', edgecolor='white', labelcolor='white')
    else:
        ax4.text(0.5, 0.5, 'No hubo días de purga', ha='center', va='center', 
                fontsize=14, color='white', transform=ax4.transAxes)
        ax4.set_title('Tipos Eliminados por Depredadores', fontsize=13, fontweight='bold', color='white')
    
    # Ajustar diseño
    plt.tight_layout()
    
    # Mostrar las gráficas
    plt.show()


def mostrar_tabla_historico(historial_estadisticas):
    """Muestra la tabla de histórico diario"""
    fig = plt.figure(figsize=(16, 10), facecolor='#1a1a1a')
    ax = fig.add_subplot(111)
    ax.axis('off')

    data_unificada = [[
        'Día', 'Población Total', 'En casa', 'Comieron',
        'Pueden Reproducirse', 'Normales', 'Verdes', 'Rojos', 'Depredadores'
    ]]

    for estad in historial_estadisticas:
        data_unificada.append([
            str(estad['dia']),
            str(estad['poblacion_total']),
            str(estad['en_casa']),
            str(estad['comieron']),
            str(estad['pueden_reproducirse']),
            str(estad['normales']),
            str(estad['verdes']),
            str(estad['rojos']),
            str(estad['depredadores'])
        ])

    table = ax.table(cellText=data_unificada, cellLoc='center', loc='center',
                     colWidths=[0.05, 0.12, 0.08, 0.08, 0.14, 0.08, 0.07, 0.07, 0.1],
                     bbox=[0, 0, 1, 0.9])
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 2.2)

    for i in range(len(data_unificada)):
        for j in range(len(data_unificada[0])):
            cell = table[(i, j)]
            if i == 0:
                cell.set_facecolor('#1a8cff')
                cell.set_text_props(weight='bold', color='white')
            else:
                cell.set_facecolor('#2d2d2d' if i % 2 == 0 else '#3a3a3a')
                cell.set_text_props(color='white')

    ax.set_title('Histórico', fontsize=14, fontweight='bold', color='white', pad=30)
    plt.tight_layout()
    plt.show()


def mostrar_tabla_depredadores(historial_depredadores):
    """Muestra la tabla de impacto de depredadores"""
    fig = plt.figure(figsize=(12, 8), facecolor='#1a1a1a')
    ax = fig.add_subplot(111)
    ax.axis('off')

    if historial_depredadores:
        data_depredadores = [['Día Purga', 'Eliminadas', 'Normales', 'Verdes', 'Rojos']]
        for dep in historial_depredadores:
            data_depredadores.append([
                str(dep['dia']),
                str(dep['particulas_eliminadas']),
                str(dep.get('normal_eliminadas', 0)),
                str(dep.get('velocidad_eliminadas', 0)),
                str(dep.get('prioridad_eliminadas', 0))
            ])

        table = ax.table(cellText=data_depredadores, cellLoc='center', loc='center',
                         colWidths=[0.18, 0.22, 0.2, 0.2, 0.2], bbox=[0, 0, 1, 0.85])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2.0)

        for i in range(len(data_depredadores)):
            for j in range(len(data_depredadores[0])):
                cell = table[(i, j)]
                if i == 0:
                    cell.set_facecolor('#1a8cff')
                    cell.set_text_props(weight='bold', color='white')
                else:
                    cell.set_facecolor('#2d2d2d' if i % 2 == 0 else '#3a3a3a')
                    cell.set_text_props(color='white')
    else:
        ax.text(0.5, 0.5, 'No hubo días de purga', ha='center', va='center',
                fontsize=14, color='white', transform=ax.transAxes)

    ax.set_title('Impacto de Depredadores', fontsize=14, fontweight='bold', color='white', pad=30)
    plt.tight_layout()
    plt.show()


def mostrar_tabla_resumen(historial_poblacion, historial_depredadores, historial_estadisticas, config):
    """Muestra la tabla de resumen de simulación"""
    fig = plt.figure(figsize=(10, 10), facecolor='#1a1a1a')
    ax = fig.add_subplot(111)
    ax.axis('off')

    data_resumen = [
        ['Métrica', 'Valor'],
        ['Población Inicial', str(historial_poblacion[0])],
        ['Población Final', str(historial_poblacion[-1])],
        ['Población Máxima', str(max(historial_poblacion))],
        ['Población Mínima', str(min(historial_poblacion))],
        ['Días de Purga', str(len(historial_depredadores))],
        ['Depredadores por Purga', str(config['depredadores'])],
        ['Frecuencia de Purga', str(config['frecuencia_purga'])],
        ['Comida (%)', str(config['comida'])],
        ['Total de Días', str(len(historial_estadisticas))]
    ]

    table = ax.table(cellText=data_resumen, cellLoc='center', loc='center',
                     colWidths=[0.55, 0.35], bbox=[0, 0, 1, 0.9])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.2)

    for i in range(len(data_resumen)):
        for j in range(len(data_resumen[0])):
            cell = table[(i, j)]
            if i == 0:
                cell.set_facecolor('#1a8cff')
                cell.set_text_props(weight='bold', color='white')
            else:
                cell.set_facecolor('#2d2d2d' if i % 2 == 0 else '#3a3a3a')
                cell.set_text_props(color='white')

    ax.set_title('Resumen de Simulación', fontsize=14, fontweight='bold', color='white', pad=30)
    plt.tight_layout()
    plt.show()


def pantalla_tablas_historico(pantalla, reloj, historial_poblacion, historial_tipos, historial_depredadores, historial_estadisticas, config):
    """Abre las tablas en ventanas separadas"""
    mostrar_tabla_historico(historial_estadisticas)
    mostrar_tabla_depredadores(historial_depredadores)
    mostrar_tabla_resumen(historial_poblacion, historial_depredadores, historial_estadisticas, config)


def pantalla_fin_simulacion(pantalla, reloj, historial_poblacion, historial_tipos, historial_depredadores, historial_estadisticas, config):
    """Pantalla final con botón para ver gráficas"""
    fuente_titulo = pygame.font.Font(None, 56)
    fuente = pygame.font.Font(None, 28)
    
    boton_graficas = Boton((ANCHO_VENTANA//2 - 90, ALTO_VENTANA//2 - 120, 180, 50), "VER GRÁFICAS", AZUL_BOTON, (102, 187, 106))
    boton_tablas = Boton((ANCHO_VENTANA//2 - 90, ALTO_VENTANA//2 - 50, 180, 50), "VER TABLAS", AZUL_BOTON, (90, 190, 255))
    boton_menu = Boton((ANCHO_VENTANA//2 - 90, ALTO_VENTANA//2 + 20, 180, 50), "MENU", AZUL_BOTON, (90, 190, 255))
    boton_salir = Boton((ANCHO_VENTANA//2 - 90, ALTO_VENTANA//2 + 90, 180, 50), "SALIR", ROJO, (200, 50, 50))
    
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
                    pantalla_graficas(pantalla, reloj, historial_poblacion, historial_tipos, historial_depredadores)
                if boton_tablas.click(evento.pos):
                    pantalla_tablas_historico(pantalla, reloj, historial_poblacion, historial_tipos, historial_depredadores, historial_estadisticas, config)
                if boton_menu.click(evento.pos):
                    return "menu"
                if boton_salir.click(evento.pos):
                    pygame.quit()
                    sys.exit()
        
        pantalla.fill(NEGRO)
        
        # Título
        titulo = fuente_titulo.render("Simulación Completada", True, CYAN)
        pantalla.blit(titulo, titulo.get_rect(center=(ANCHO_VENTANA//2, 80)))
        
        boton_graficas.dibujar(pantalla, fuente)
        boton_tablas.dibujar(pantalla, fuente)
        boton_menu.dibujar(pantalla, fuente)
        boton_salir.dibujar(pantalla, fuente)
        
        pygame.display.flip()
        reloj.tick(60)

    return None


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
            config["depredadores"],
            config["frecuencia_purga"]
        )
        
        # Si resultado es (None, None, None), el usuario quiere volver al menú
        if resultado == (None, None, None, None):
            continue
        
        # Si llegamos aquí, la simulación terminó naturalmente
        historial_poblacion, historial_tipos, historial_depredadores, historial_estadisticas = resultado
        
        # Mostrar pantalla final con opciones
        resultado_fin = pantalla_fin_simulacion(pantalla, reloj, historial_poblacion, historial_tipos, historial_depredadores, historial_estadisticas, config)
        if resultado_fin == "menu":
            continue
        break


if __name__ == "__main__":
    main()
