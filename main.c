#include "project.h"
#include "stdio.h"

#define MSG_LEN 64
char msg[MSG_LEN];

int main(void)
{
    CyGlobalIntEnable;  // Habilitar interrupciones globales

    // === Inicializar componentes ===
    ADC_SAR_1_Start();
    ADC_SAR_1_StartConvert();
    USBUART_1_Start(0u, USBUART_1_5V_OPERATION);

    // Esperar conexión USB (CDC configurado)
    while (!USBUART_1_GetConfiguration());
    USBUART_1_CDC_Init();

    for (;;)
    {
        // Esperar fin de conversión
        ADC_SAR_1_IsEndConversion(ADC_SAR_1_WAIT_FOR_RESULT);

        // Leer resultado y convertir a voltaje
        int16 adcCounts = ADC_SAR_1_GetResult16();

        // Formatear texto
        sprintf(msg, "%i\r\n", adcCounts);

        // Enviar por USB (CDC)
        if (USBUART_1_CDCIsReady())
            USBUART_1_PutString(msg);

        CyDelay(1);  // 10 ms entre muestras
    }
}
