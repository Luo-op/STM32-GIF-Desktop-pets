#ifndef __OLED_H
#define __OLED_H

#include "stm32f10x.h"

#define OLED_SCL_PIN    GPIO_Pin_8
#define OLED_SDA_PIN    GPIO_Pin_9
#define OLED_GPIO_PORT  GPIOB
#define RCC_OLED_PORT   RCC_APB2Periph_GPIOB

#define SH1106_ADDR     0x3C
#define NUM_FRAMES      22
#define FRAME_DELAY     0U

extern const uint8_t frame_1[1024];
extern const uint8_t frame_2[1024];
extern const uint8_t frame_3[1024];
extern const uint8_t frame_4[1024];
extern const uint8_t frame_5[1024];
extern const uint8_t frame_6[1024];
extern const uint8_t frame_7[1024];
extern const uint8_t frame_8[1024];
extern const uint8_t frame_9[1024];
extern const uint8_t frame_10[1024];
extern const uint8_t frame_11[1024];
extern const uint8_t frame_12[1024];
extern const uint8_t frame_13[1024];
extern const uint8_t frame_14[1024];
extern const uint8_t frame_15[1024];
extern const uint8_t frame_16[1024];
extern const uint8_t frame_17[1024];
extern const uint8_t frame_18[1024];
extern const uint8_t frame_19[1024];
extern const uint8_t frame_20[1024];
extern const uint8_t frame_21[1024];
extern const uint8_t frame_22[1024];

extern const uint8_t* const frames[NUM_FRAMES];

void SH1106_Init(void);
void SH1106_DisplayFrame(const uint8_t *frame_buf);
void SH1106_PlayAnim(void);

#endif