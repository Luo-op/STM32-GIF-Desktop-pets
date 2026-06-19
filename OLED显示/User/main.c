#include "stm32f10x.h"
#include "OLED.h"

int main(void)
{
    SH1106_Init();
    while(1)
    {
        SH1106_PlayAnim();
    }
}