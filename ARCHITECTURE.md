# 🤖 AgenTra - Arquitectura del Bot de Trading

> Documento de referencia rápida sobre cómo funciona el bot.  
> Última actualización: 2026-01-30

---

## 🔄 Ciclos de Operación

El bot tiene **3 ciclos independientes**:

### 1. Micro-Loop (Trailing Stop) - Cada 3-15 segundos
```
¿QUÉ HACE?
→ Pide el precio spot actual (1 request ligero)
→ Compara con el Stop Loss de posiciones activas
→ Mueve el trailing stop si el precio mejora
→ Verifica si TP o SL fueron alcanzados

NO HACE:
✗ No pide velas
✗ No recalcula indicadores
✗ No toma decisiones de entrada
```

### 2. Macro-Loop (Análisis) - Cada 3-5 minutos
```
¿QUÉ HACE?
→ Pide velas de 15 minutos (últimas 100)
→ Calcula indicadores: RSI, ATR, VPIN, ADX, etc.
→ Detecta niveles de S/R cercanos
→ Consulta a la AI (Gemini) si hay setup válido
→ Decide entradas/salidas

PARA:
• Nuevas entradas
• Análisis técnico completo
• Detección de oportunidades
```

### 3. Structure-Loop (Estructura 4H) - Cada 4 horas
```
¿QUÉ HACE?
→ Pide velas de 4 horas (últimas 252 = 6 semanas)
→ Detecta Swing Highs y Swing Lows
→ Calcula BOS (Break of Structure)
→ Detecta CHoCH (Change of Character)
→ Actualiza el bias en state.json

PARA:
• Determinar si estamos en tendencia BULLISH o BEARISH
• Detectar cambios de tendencia
• Filtrar entradas contra la estructura
```

---

## 📊 Jerarquía de Decisión

```
            ┌─────────────────────────────────────┐
            │  4H: ¿Cuál es la tendencia macro?   │
            │  BOS/CHoCH → bias BULLISH/BEARISH   │
            └─────────────────────────────────────┘
                            │
                            ▼
            ┌─────────────────────────────────────┐
            │  15m: ¿Hay setup cerca de S/R?      │
            │  Solo SHORT cerca de resistencia    │
            │  Solo LONG cerca de soporte         │
            └─────────────────────────────────────┘
                            │
                            ▼
            ┌─────────────────────────────────────┐
            │  Indicadores + AI: ¿Es válido?      │
            │  RSI, VPIN, FVG, MACD, etc.         │
            │  Gemini evalúa confluencias         │
            └─────────────────────────────────────┘
                            │
                            ▼
            ┌─────────────────────────────────────┐
            │  ENTRADA → Si todo confirma         │
            │  Trailing progresivo activo         │
            └─────────────────────────────────────┘
```

---

## 🗂️ Archivos Clave

| Archivo | Propósito |
|---------|-----------|
| `main.py` | Loop principal, gestión de posiciones, trailing |
| `trading_tools.py` | Funciones de análisis, indicadores, API |
| `state.json` | Estado persistente: posiciones, balance, historial |
| `radiografias.md` | Log detallado de cada operación |
| `BOS.md` | Documentación de estrategia avanzada |
| `playbooks.json` | Configuración de estrategias activas |

---

## 💾 Persistencia (state.json)

Lo que se guarda entre reinicios:
- Balance actual
- Posiciones abiertas
- Historial de trades
- Métricas de rendimiento
- **Estructura de mercado (4H bias)** ← Nuevo

---

## 🎯 Pares Activos

- **ETH/USDT** - Principal
- **LINK/USDT** - Baja correlación con BTC (próximo)
- **AAVE/USDT** - DeFi independiente (próximo)

---

## 📝 Reglas de Oro

1. **Nunca operar contra la estructura 4H**
2. **Solo entrar cerca de S/R**
3. **CHoCH = Pausar y reevaluar**
4. **Trailing protege ganancias, no las garantiza**

---

## 🔧 Para Actualizar

Cuando hagas cambios, recuerda:
1. Probar con `python -m py_compile main.py`
2. Verificar que no rompe state.json
3. Documentar cambios aquí si afectan la arquitectura
