#include <8051.h>

int main()
{
    unsigned char i, j;
    unsigned char button = 0;
    unsigned char massiv[11] = {
        0xC0,
        0xF9,
        0xA4,
        0xB0,
        0x99,
        0x92,
        0x82,
        0xF8,
        0x80,
        0x90,
        0xFF
    };
    unsigned char current_index = 0;
    unsigned char mod2_index = 0;
    unsigned char mod2_flag = 0;

    P1 = massiv[10];

    while (1) {
        if ((P3 & 0x02) == 0) {
            if (!mod2_flag) {
                mod2_index = current_index / 2;
                if (current_index % 2 != 0) {
                    mod2_index++;
                }
                mod2_index %= 5;
            }
            mod2_flag = 1;
            button = 1;
        }
        else {
            mod2_flag = 0;
            button = 0;
        }
        if (mod2_flag) {
            P2 = massiv[mod2_index * 2];
            for (j = 0; j < 200; j++);
            mod2_index++;
            if (mod2_index >= 5) {
                mod2_index = 0;
            }
        }
        else {
            P2 = massiv[current_index];
            for (j = 0; j < 200; j++);
            current_index++;
            if (current_index >= 10) {
                current_index = 0;
            }
        }
    }
    return 0;
}
