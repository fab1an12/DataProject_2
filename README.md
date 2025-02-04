# Flujo de conversación del bot de emergencia

## 1. Contexto inicial
**Mensaje de bienvenida del bot:**  
"Hola, soy un asistente de emergencia. Estoy aquí para ayudarte. Cuéntame tu situación y trataré de encontrar ayuda lo antes posible."

---

## 2. Tipo de necesidad
**Bot:**  
"Para entender mejor cómo ayudarte, ¿qué es lo que más necesitas en este momento? Puedes explicarlo con tus palabras."

**Inferencias del LLM:**  
- **Asistencia médica:** "Estoy herido", "Alguien aquí necesita un médico".
- **Evacuación/transporte:** "Necesitamos salir de aquí", "Estamos atrapados".
- **Refugio:** "No tengo dónde quedarme", "Necesito un lugar seguro".
- **Suministros:** "Nos falta comida y agua", "Necesitamos medicamentos".
- **Rescate:** "Estamos atrapados bajo escombros", "No podemos salir del edificio".

Si la respuesta es ambigua, el bot pregunta:  
"Entiendo. ¿Podrías decirme si necesitas ayuda médica, transporte, refugio, comida o rescate?"

---

## 3. Ubicación
**Bot:**  
"¿Dónde estás ahora? Puedes enviarme tu ubicación o describir dónde te encuentras."

**Inferencias del LLM:**  
- Se envía ubicación en Telegram, se extraen las coordenadas.

---

## 4. Número de personas afectadas
**Bot:**  
"¿Estás solo o hay más personas contigo? Si es así, ¿cuántas necesitan ayuda?"

**Inferencias del LLM:**  
- Extraer el número de afectados.
- Si la respuesta es vaga ("estamos varias personas"), preguntar:  
  "Para enviar la ayuda correcta, ¿podrías decirme cuántos son en total?"

---

## 5. Nivel de urgencia
**Bot:**  
"¿Qué tan urgente es la ayuda que necesitas? Puedes decirme si es una emergencia crítica o si puedes esperar un poco."

**Inferencias del LLM:**  
- **Crítica (5/5):** Vida en peligro inmediato ("Estoy atrapado", "Alguien está muy herido", "Hay un incendio cerca").
- **Alta (4/5):** Necesidad urgente pero no de vida o muerte ("No tenemos agua desde hace días", "Estamos expuestos al frío", "No podemos salir de aquí").
- **Media (3/5):** Puede esperar algunas horas.
- **Baja (1-2/5):** Ayuda necesaria pero no inmediata.

---

## 6. Confirmación y envío de solicitud
**Bot:**  
"Voy a enviar tu solicitud ahora. Estos son los detalles que tengo:"

- **Ubicación:** [ubicación]  
- **Personas afectadas:** [número]  
- **Tipo de ayuda:** [tipo]  
- **Urgencia:** [nivel]  
- **Contacto:** [info]  