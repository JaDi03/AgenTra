# 🗺️ ROADMAP: Quant & AI Upgrades for AgenTra
*Propuestas de Nivel Institucional para Futuras Iteraciones*

Este documento recopila las sugerencias avanzadas de la auditoría externa para convertir al bot en un sistema de trading adaptativo de grado institucional.

## 1. La Capa Metacognitiva: Ensemble de Estrategias
> **Objetivo:** Evitar la fragilidad de una única estrategia.
- [x] **Implementar Selector de Estrategias:** Crear un diccionario de estrategias (`Trend`, `MeanReversion`, `Breakout`).
    - **Trend (Actual):** EMA + RSI + ATR Trailing Stop.
    - **Mean Reversion (NUEVO):** Para mercados en Rango (Hurst < 0.4).
        - *Logic:* Ornstein-Uhlenbeck (Reversión a la media matemática).
        - *Exits:* Time Stop (Half-life) y Structural Stop (fuera del Value Area Low/High).

**falta activar ameta-Learner** ---------------------------------
- [ ] **Meta-Learner (EXP3):** Algoritmo que asigne peso/capital dinámicamente a la estrategia que mejor esté funcionando en la última semana.

## 1.1 Clasificación de Régimen (El Cerebro Dual)
- [x] **Exponente de Hurst (H):** Métrica definitiva para separar Trend vs Rango.
    - H > 0.6: Activar Trend Strategy.
    - H < 0.4: Activar Mean Reversion Strategy.
- [x] **Volume Profile (Mapa del Rango):** Usar POC y Value Area (VA) para definir Stops Estructurales en lugar de ATR ciego.

## 2. Sistema Inmunológico: Detección de "Concept Drift"
> **Objetivo:** Saber cuándo las reglas del mercado han cambiado.
- [x] **Kolmogorov-Smirnoff Test:** (COMPLETO: Implementado en `market_monitor.py` y auditado).
- [x] **Protocolo de Congelamiento:** (COMPLETO: Alerta inyectada en Prompt y modo DEFENSIVE forzado).
- [x] **Drift Estadístico Puro:** Implementado KS-test real para validar la distribución de retornos.

## 3. Microestructura Avanzada: VPIN Real
> **Objetivo:** Detectar flujo tóxico (institucionales cazando stops).
- [x] **VPIN Pro:** (COMPLETO: Implementado algoritmo de Volume Buckets en `order_flow.py`).
- [x] **Filtro Transaccional:** El bot bloquea entradas si VPIN > 0.7 (Informed Trading detected).

## 4. Memoria Dinámica: Online Learning
> **Objetivo:** Olvidar datos obsoletos inteligentemente.
- [ ] **EWRLS (Exponentially Weighted Recursive Least Squares):** Para ajustar los pesos de las estrategias con un factor de olvido (ej. 0.99).

## 5. Walk-Forward Validator (Anti-Overfitting)
> **Objetivo:** Validar cambios antes de aplicarlos.
- [ ] **Clase Validator:** Antes de aceptar un cambio propuesto por la IA, correr una simulación rápida en datos pasados recientes (Training vs Testing set) para asegurar que no es ruido.

## 6. Gestión de Capital Adaptativa (Kelly Criterion)
> **Objetivo:** Apostar más cuando la probabilidad de ganar es alta.
- [ ] **Fractional Kelly:** Ajustar el tamaño de la posición no solo por ATR, sino por la "confianza estadística" del Edge actual.

---
*Este roadmap servirá de guía para la evolución continua del proyecto después de estabilizar la "Arquitectura Forense" actual.*
