# Datos de prueba

CSV **sintéticos** con las columnas de PaySim para probar `POST /api/v1/predict/batch`
sin descargar el dataset completo. No son datos reales de PaySim.

| Archivo | Filas | Para qué |
|---|---|---|
| `transactions_1k.csv` | 1 000 (~2 % fraude) | Pruebas normales desde el front o Swagger |
| `transactions_10k.csv` | 10 000 (~2 % fraude) | Rendimiento; es el máximo de `max_batch_rows` |
| `transactions_invalid.csv` | 6 (5 rotas) | Debe devolver 422 |

- La columna `isFraud` es la etiqueta esperada. La API la ignora y sirve para comparar con lo que predice el modelo.
- El fraude imita el patrón de PaySim: solo `TRANSFER` y `CASH_OUT`, y vacía la cuenta de origen.
- Hay algunos casos borde válidos: monto enorme, todo en cero, saldo de origen 0 con monto alto y filas sin nombres de cuenta.

Para regenerarlos (semilla fija, salen iguales):

```bash
python scripts/generate_sample.py
```

`tests/test_sample_data.py` comprueba que sigan pasando el schema y la API.
