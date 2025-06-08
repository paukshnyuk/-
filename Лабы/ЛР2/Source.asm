.686
.model flat,stdcall
.stack 100h

ExitProcess PROTO STDCALL :DWORD

.data
arr1 dw 00001h, 07844h, 0AD43h, 05622h   ; X, Y, Z, Q
arr2 dw 4 dup (?)                        ; X', Y', Z', Q'
L    dw ?                                ; Сумма элементов arr2
M    dw ?
R    dw ?

.code
Start:
    mov ecx, 4               ; Счётчик для 4 элементов
    mov esi, offset arr1     ; Указатель на arr1
    mov edi, offset arr2     ; Указатель на arr2
    xor ebx, ebx             ; Обнуляем сумму

cycle_inc:
    mov ax, [esi]            ; Загружаем очередной элемент из arr1
    inc ax                   
    mov [edi], ax            ; Сохраняем в arr2
    add bx, ax               ; Прибавляем к сумме
    add esi, 2               ; Переход к следующему элементу
    add edi, 2
    loop cycle_inc           

    mov L, bx                ; Сохраняем сумму в L

    ; M = (L AND X') - (L AND Y')
    mov ax, L
    mov dx, [arr2]           ; X'
    and ax, dx
    mov cx, ax

    mov ax, L
    mov dx, [arr2+2]         ; Y'
    and ax, dx
    sub cx, ax
    mov M, cx

    ; Если M >= 921Bh, то переход к Proc1, иначе к Proc2
    mov ax, M
    cmp ax, 921Bh
    jge  Proc1_call
    jmp  Proc2_call

Proc1_call:
    Call Proc1
    Call CheckEven

Proc2_call:
    Call Proc2
    Call CheckEven

Proc1:
    ; R = M / 2 - 12B9h
    mov ax, M
    shr ax, 1
    sub ax, 12B9h
    mov R, ax
    Call CheckEven
    ret

Proc2:
    ; R = M - Q'/2
    mov ax, [arr2+6]         ; Q'
    shr ax, 1
    mov bx, M
    sub bx, ax
    mov R, bx
    ret

CheckEven:
    mov ax, R
    test ax, 1               ; Проверка на чётность
    Call HandleEven

Odd:
    dec ax                   ; Если нечётное, уменьшаем на 1
    Call Done

HandleEven:
    or ax, 009Fh             ; Если чётное
    Call Done

Done:
    mov R, ax
    invoke ExitProcess, 0
End Start
