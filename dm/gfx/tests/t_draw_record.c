// Command records from damaged or overwritten guest memory must not copy past the payload.
#include <assert.h>
#include <stdint.h>
#include <string.h>
#include "../nvn/nvn_obj.h"

int main(void) {
    assert(op_hdr_valid((op_hdr){OP_END, 8}));
    assert(op_hdr_valid((op_hdr){OP_DRAW, 8 + offsetof(p_draw, ind)}));
    assert(!op_hdr_valid((op_hdr){OP_DRAW, 0}));
    assert(!op_hdr_valid((op_hdr){OP_DRAW, 7}));
    assert(!op_hdr_valid((op_hdr){OP_DRAW, 9}));
    assert(!op_hdr_valid((op_hdr){OP_COUNT_, 8}));
    assert(!op_hdr_valid((op_hdr){OP_CALL, 8}));
    assert(!op_hdr_valid((op_hdr){OP_JUMP, 8}));
    assert(!op_hdr_valid((op_hdr){OP_SIGNAL_EVENT, 16}));
    assert(!op_hdr_valid((op_hdr){OP_COPY_B2B, 24}));
    assert(op_hdr_valid((op_hdr){OP_CALL, 16}));
    assert(op_hdr_valid((op_hdr){OP_SIGNAL_EVENT, 24}));
    assert(op_hdr_valid((op_hdr){OP_COPY_B2B, 32}));
    uint8_t raw[sizeof(p_draw_idx) + 16];
    memset(raw, 0x5a, sizeof raw);
    p_draw draw, zero_draw = {0};
    p_draw_idx idx, zero_idx = {0};
    for (uint32_t size = 0; size < 8; size++) {
        assert(draw_rec(raw, size, &draw) == &draw);
        assert(draw_idx_rec(raw, size, &idx) == &idx);
        assert(memcmp(&draw, &zero_draw, sizeof draw) == 0);
        assert(memcmp(&idx, &zero_idx, sizeof idx) == 0);
    }
    for (uint32_t size = 9; size < 8 + offsetof(p_draw, ind); size++) {
        assert(draw_rec(raw, size, &draw) == &draw);
        assert(memcmp(&draw, &zero_draw, sizeof draw) == 0);
    }
    assert(draw_rec(raw, 8 + offsetof(p_draw, ind), &draw) == &draw);
    assert(draw.count == 0x5a5a5a5a && draw.ind == 0);
    assert(draw_rec(raw, 8 + sizeof draw, &draw) == (const p_draw *)raw);
    assert(draw_idx_rec(raw, 8 + offsetof(p_draw_idx, ind), &idx) == &idx);
    assert(idx.count == 0x5a5a5a5a && idx.ind == 0);
    assert(draw_idx_rec(raw, 8 + sizeof idx, &idx) == (const p_draw_idx *)raw);
    assert(draw_rec(raw, UINT32_MAX, &draw) == &draw);
    assert(draw_idx_rec(raw, UINT32_MAX, &idx) == &idx);
    return 0;
}
