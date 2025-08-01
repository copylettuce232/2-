import pygame
import random
import sys
import time # 애니메이션 타이밍을 위해

# --- 상수 설정 ---
BOARD_SIZE = 4
TILE_SIZE = 100 # 타일 하나의 픽셀 크기
GAP = 10 # 타일 간 간격
BOARD_WIDTH = BOARD_HEIGHT = BOARD_SIZE * TILE_SIZE + (BOARD_SIZE + 1) * GAP
SCREEN_WIDTH = BOARD_WIDTH + 100 # 화면 너비 (여백 포함)
SCREEN_HEIGHT = BOARD_HEIGHT + 150 # 화면 높이 (헤더/버튼 공간 포함)

# 색상 정의
WHITE = (255, 255, 255)
LIGHT_ORANGE_BG = (255, 224, 178) # 게임 컨테이너 배경색 #ffe0b2
GRID_CELL_COLOR = (128, 128, 128, 50) # 격자 셀 색상 (투명도 포함)
TEXT_COLOR = (119, 110, 101) # 타일 숫자 텍스트 색상 #776e65
BUTTON_COLOR = (255, 138, 101) # 다시 시작 버튼 색상 #ff8a65
BUTTON_HOVER_COLOR = (255, 112, 67) # 다시 시작 버튼 호버 색상 #ff7043
START_BUTTON_COLOR = (139, 195, 74) # 시작 버튼 색상 #8bc34a
START_BUTTON_HOVER_COLOR = (124, 179, 66) # 시작 버튼 호버 색상 #7cb342
WIN_COLOR = (0, 128, 0) # 승리 메시지 색상 (순수한 초록색)
LOSE_COLOR = (255, 215, 0) # 패배 메시지 색상 (골든로드)
BLACK = (0, 0, 0) # 테두리 색상으로 사용할 검은색 추가

# 타일 값에 따른 색상 정의
TILE_COLORS = {
    0: (205, 193, 180), # 빈 셀 배경색
    2: (238, 228, 218),
    4: (237, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 94, 59),
    128: (237, 207, 114),
    256: (237, 204, 97),
    512: (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46)
}
SUPER_TILE_COLOR = (60, 58, 50) # 2048 이상 타일 색상 #3c3a32

# 합쳐질 때 나타나는 서브리미널 메시지
SUBLIMINAL_MESSAGES = [
    "You’ve got this!",
    "Keep going, you’re doing great!",
    "Be proud of how far you’ve come!",
    "Your potential is endless!"
]

# 애니메이션 설정
MERGE_ANIMATION_DURATION = 0.3 # 타일 합쳐짐 애니메이션 지속 시간 (초)
SUBLIMINAL_MESSAGE_DURATION = 0.7 # 서브리미널 메시지 지속 시간 (초)
MOVE_ANIMATION_DURATION = 0.15 # 타일 이동 애니메이션 지속 시간 (초)

# --- Tile 클래스 정의 (타일 애니메이션을 위해) ---
class Tile:
    def __init__(self, value, row, col, tile_id):
        self.value = value
        self.id = tile_id
        self.current_row = row # 현재 논리적 행
        self.current_col = col # 현재 논리적 열
        # 애니메이션 시작 픽셀 위치는 타일이 생성될 때의 위치
        self.start_x, self.start_y = get_tile_pixel_pos(row, col) 
        # 애니메이션 끝 픽셀 위치는 처음에는 시작 위치와 동일
        self.end_x, self.end_y = get_tile_pixel_pos(row, col) 
        self.animation_start_time = time.time() # 애니메이션 시작 시간
        self.is_new = True # 새로 생성된 타일 (페이드인 애니메이션용)
        self.is_merged_result = False # 합쳐짐의 결과로 생성된 타일 (펄스 애니메이션용)
        self.is_disappearing = False # 합쳐져서 사라지는 타일 (페이드아웃 애니메이션용)
        self.alpha = 255 # 투명도 (0-255)

# --- 게임 상태 변수 ---
game_board_state = [] # 게임 보드 (Tile 객체 또는 None 저장)
next_tile_id = 0 # 다음 타일에 할당할 고유 ID
all_active_tiles = [] # 현재 화면에 그려져야 할 모든 Tile 객체 (이동 중이거나 고정된 타일 포함)
active_subliminal_messages = [] # 활성화된 서브리미널 메시지 리스트

# --- Pygame 초기 설정 ---
pygame.init()
pygame.display.set_caption("2048 게임") # 창 제목
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)) # 화면 크기 설정
clock = pygame.time.Clock() # 프레임 속도 제어를 위한 Clock 객체

# 폰트 로드 (Jua.ttf 파일이 없으면 기본 폰트 사용)
try:
    font_jua_large = pygame.font.Font("Jua.ttf", 60)
    font_jua_medium = pygame.font.Font("Jua.ttf", 36)
    font_jua_small = pygame.font.Font("Jua.ttf", 24)
    font_jua_subliminal = pygame.font.Font("Jua.ttf", 28) # 문구 크기 28로 변경
    font_jua_title = pygame.font.Font("Jua.ttf", 80)
except:
    print("Jua.ttf 폰트를 찾을 수 없습니다. Pygame 기본 폰트를 사용합니다.")
    font_jua_large = pygame.font.Font(None, 60)
    font_jua_medium = pygame.font.Font(None, 36)
    font_jua_small = pygame.font.Font(None, 24)
    font_jua_subliminal = pygame.font.Font(None, 28) # 문구 크기 28로 변경
    font_jua_title = pygame.font.Font(None, 80)

# --- 헬퍼 함수 ---

def get_tile_pixel_pos(row, col):
    """
    타일의 픽셀 위치를 계산합니다.
    게임 보드의 좌측 상단 오프셋을 고려합니다.
    """
    board_offset_x = (SCREEN_WIDTH - BOARD_WIDTH) // 2
    board_offset_y = (SCREEN_HEIGHT - BOARD_HEIGHT) // 2 + 30 + 60 # 게임 컨테이너 헤더 아래
    
    x = board_offset_x + GAP + col * (TILE_SIZE + GAP)
    y = board_offset_y + GAP + row * (TILE_SIZE + GAP) 
    return x, y

def draw_rounded_rect(surface, color, rect, radius, border_width=0, border_color=(0,0,0)):
    """
    둥근 모서리 사각형을 그립니다.
    Pygame은 기본적으로 둥근 모서리를 지원하지 않으므로, border_radius를 사용하여 근사치를 그립니다.
    """
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border_width > 0:
        # 테두리는 별도의 사각형으로 그립니다.
        pygame.draw.rect(surface, border_color, rect, border_width, border_radius=radius)

def get_tile_color(value):
    """주어진 타일 값에 해당하는 색상을 반환합니다."""
    if value >= 2048:
        return SUPER_TILE_COLOR
    return TILE_COLORS.get(value, TILE_COLORS[0]) # 기본적으로 빈 셀 색상 반환

# --- 게임 로직 함수 ---

def initialize_game():
    """게임 보드와 상태를 초기화합니다."""
    global game_board_state, is_game_over, is_game_won, active_subliminal_messages, next_tile_id, all_active_tiles, is_game_started 
    game_board_state = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    is_game_over = False
    is_game_won = False
    is_game_started = False 
    active_subliminal_messages = []
    all_active_tiles = []
    next_tile_id = 0

def add_random_tile():
    """무작위 빈 공간에 새 타일 (2 또는 4)을 추가합니다."""
    global next_tile_id 
    empty_cells = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if game_board_state[r][c] is None:
                empty_cells.append((r, c))

    if empty_cells:
        r, c = random.choice(empty_cells)
        value = 2 if random.random() < 0.9 else 4
        new_tile = Tile(value, r, c, next_tile_id) 
        game_board_state[r][c] = new_tile
        all_active_tiles.append(new_tile) 
        next_tile_id += 1 
        return True
    return False

def is_board_full():
    """보드가 완전히 채워졌는지 확인합니다."""
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if game_board_state[r][c] is None:
                return False
    return True

def can_move():
    """이동 가능한 타일이 있는지 확인합니다 (게임 오버 조건)."""
    if not is_board_full():
        return True # 빈 공간이 있으면 이동 가능

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            current_tile = game_board_state[r][c]
            if current_tile is None: continue

            # 오른쪽 타일과 비교
            if c < BOARD_SIZE - 1:
                other_tile = game_board_state[r][c+1]
                if other_tile is None or other_tile.value == current_tile.value:
                    return True
            # 아래쪽 타일과 비교
            if r < BOARD_SIZE - 1:
                other_tile = game_board_state[r+1][c]
                if other_tile is None or other_tile.value == current_tile.value:
                    return True
    return False # 이동할 수 있는 타일이 없음

def slide_and_merge_line(line_of_tiles, is_reverse):
    """
    한 줄 (행 또는 열)의 타일을 이동하고 합칩니다.
    Tile 객체를 직접 처리하며, 병합된 타일과 사라지는 타일을 반환합니다.
    """
    filtered_tiles = [tile for tile in line_of_tiles if tile is not None]

    processed_tiles = []
    merged_results_for_animation = [] 
    disappearing_tiles_for_animation = [] 

    if is_reverse: # 오른쪽 또는 아래로 이동 (moves to end of list)
        i = len(filtered_tiles) - 1
        while i >= 0:
            current_tile = filtered_tiles[i]
            if i > 0 and filtered_tiles[i-1].value == current_tile.value:
                # 병합
                merged_value = current_tile.value * 2
                kept_tile = filtered_tiles[i-1] 
                
                # kept_tile의 속성 업데이트
                kept_tile.value = merged_value
                kept_tile.is_merged_result = True
                kept_tile.animation_start_time = time.time() 

                # 사라지는 타일
                disappearing_tile = current_tile
                disappearing_tile.is_disappearing = True
                disappearing_tile.animation_start_time = time.time()
                disappearing_tiles_for_animation.append(disappearing_tile)

                processed_tiles.insert(0, kept_tile) 
                merged_results_for_animation.append(kept_tile)
                i -= 2 
            else:
                processed_tiles.insert(0, current_tile) 
                i -= 1
        new_line = [None] * (BOARD_SIZE - len(processed_tiles)) + processed_tiles 
    else: # 왼쪽 또는 위로 이동 (moves to beginning of list)
        i = 0
        while i < len(filtered_tiles):
            current_tile = filtered_tiles[i]
            if i + 1 < len(filtered_tiles) and filtered_tiles[i+1].value == current_tile.value:
                # 병합
                merged_value = current_tile.value * 2
                kept_tile = current_tile 
                
                # kept_tile의 속성 업데이트
                kept_tile.value = merged_value
                kept_tile.is_merged_result = True
                kept_tile.animation_start_time = time.time()

                # 사라지는 타일
                disappearing_tile = filtered_tiles[i+1]
                disappearing_tile.is_disappearing = True
                disappearing_tile.animation_start_time = time.time()
                disappearing_tiles_for_animation.append(disappearing_tile)

                processed_tiles.append(kept_tile)
                merged_results_for_animation.append(kept_tile)
                i += 2 
            else:
                processed_tiles.append(current_tile)
                i += 1
        new_line = processed_tiles + [None] * (BOARD_SIZE - len(processed_tiles))
    return new_line, merged_results_for_animation, disappearing_tiles_for_animation

def move(direction):
    """방향에 따라 타일 이동을 처리합니다."""
    global game_board_state, all_active_tiles, active_subliminal_messages
    
    # 이동 전 보드 상태를 깊은 복사하여 저장 (타일 객체 참조 유지)
    old_board_state = [[game_board_state[r][c] for c in range(BOARD_SIZE)] for r in range(BOARD_SIZE)]
    
    moved_anything = False
    merged_result_tiles_for_messages = []
    
    # 모든 활성 타일의 애니메이션 시작 위치를 현재 위치로 설정하고 플래그 초기화
    for tile in all_active_tiles:
        # 현재 논리적 위치를 기반으로 start_x, start_y를 다시 계산
        tile.start_x, tile.start_y = get_tile_pixel_pos(tile.current_row, tile.current_col)
        tile.animation_start_time = time.time()
        tile.is_new = False
        tile.is_merged_result = False
        tile.is_disappearing = False

    # 임시 새 보드 상태 생성
    temp_new_board_state = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    
    # 사라질 타일들을 임시로 저장 (all_active_tiles에 추가될 것임)
    temp_disappearing_tiles = []

    if direction == 'left':
        for r in range(BOARD_SIZE):
            line_of_tiles = [old_board_state[r][c] for c in range(BOARD_SIZE)]
            # 'left' 방향은 is_reverse=False (시작점 방향으로 이동)
            new_line, merged_results, disappearing = slide_and_merge_line(line_of_tiles, False) 
            for c in range(BOARD_SIZE):
                temp_new_board_state[r][c] = new_line[c]
                if new_line[c] is not None:
                    new_line[c].current_row = r
                    new_line[c].current_col = c
                    new_line[c].end_x, new_line[c].end_y = get_tile_pixel_pos(r, c)
            merged_result_tiles_for_messages.extend(merged_results)
            temp_disappearing_tiles.extend(disappearing)

    elif direction == 'right':
        for r in range(BOARD_SIZE):
            line_of_tiles = [old_board_state[r][c] for c in range(BOARD_SIZE)]
            # 'right' 방향은 is_reverse=True (끝점 방향으로 이동)
            new_line, merged_results, disappearing = slide_and_merge_line(line_of_tiles, True) 
            for c in range(BOARD_SIZE):
                temp_new_board_state[r][c] = new_line[c]
                if new_line[c] is not None:
                    new_line[c].current_row = r
                    new_line[c].current_col = c
                    new_line[c].end_x, new_line[c].end_y = get_tile_pixel_pos(r, c)
            merged_result_tiles_for_messages.extend(merged_results)
            temp_disappearing_tiles.extend(disappearing)

    elif direction == 'up':
        for c in range(BOARD_SIZE):
            line_of_tiles = [old_board_state[r][c] for r in range(BOARD_SIZE)]
            # 'up' 방향은 is_reverse=False (시작점 방향으로 이동)
            new_col, merged_results, disappearing = slide_and_merge_line(line_of_tiles, False) 
            for r in range(BOARD_SIZE):
                temp_new_board_state[r][c] = new_col[r]
                if new_col[r] is not None:
                    new_col[r].current_row = r
                    new_col[r].current_col = c
                    new_col[r].end_x, new_col[r].end_y = get_tile_pixel_pos(r, c)
            merged_result_tiles_for_messages.extend(merged_results)
            temp_disappearing_tiles.extend(disappearing)

    elif direction == 'down':
        for c in range(BOARD_SIZE):
            line_of_tiles = [old_board_state[r][c] for r in range(BOARD_SIZE)]
            # 'down' 방향은 is_reverse=True (끝점 방향으로 이동)
            new_col, merged_results, disappearing = slide_and_merge_line(line_of_tiles, True) 
            for r in range(BOARD_SIZE):
                temp_new_board_state[r][c] = new_col[r]
                if new_col[r] is not None:
                    new_col[r].current_row = r
                    new_col[r].current_col = c
                    new_col[r].end_x, new_col[r].end_y = get_tile_pixel_pos(r, c)
            merged_result_tiles_for_messages.extend(merged_results)
            temp_disappearing_tiles.extend(disappearing)

    # 보드에 변화가 있었는지 확인 (이동 또는 병합)
    old_tile_ids = set()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if old_board_state[r][c] is not None:
                old_tile_ids.add(old_board_state[r][c].id)
    
    new_tile_ids = set()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if temp_new_board_state[r][c] is not None:
                new_tile_ids.add(temp_new_board_state[r][c].id)

    if old_tile_ids != new_tile_ids: 
        moved_anything = True
    else: 
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                old_tile = old_board_state[r][c]
                new_tile = temp_new_board_state[r][c]
                if (old_tile is None and new_tile is not None) or \
                   (old_tile is not None and new_tile is None) or \
                   (old_tile is not None and new_tile is not None and \
                    (old_tile.id != new_tile.id or old_tile.value != new_tile.value)):
                    moved_anything = True
                    break
            if moved_anything:
                break

    if moved_anything:
        game_board_state = temp_new_board_state 
        add_random_tile() 

        # 병합된 타일에 대한 서브리미널 메시지 트리거
        for tile in merged_result_tiles_for_messages:
            show_subliminal_message(tile.current_row, tile.current_col)
        
        # all_active_tiles 목록을 재구성:
        updated_active_tiles = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if game_board_state[r][c] is not None:
                    updated_active_tiles.append(game_board_state[r][c])
        
        # 사라지는 타일 중 애니메이션이 끝나지 않은 타일만 추가
        for tile in temp_disappearing_tiles:
            if tile.is_disappearing: 
                updated_active_tiles.append(tile)
        
        all_active_tiles = updated_active_tiles
        return True
    return False

def check_game_status():
    """승리/패배 조건을 확인합니다."""
    global is_game_over, is_game_won
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            current_tile = game_board_state[r][c]
            if current_tile is not None and current_tile.value == 2048:
                is_game_won = True
                end_game('win')
                return

    if not can_move():
        is_game_over = True
        end_game('lose')

def end_game(status):
    """게임 종료 및 결과 메시지를 표시합니다."""
    global is_game_started 
    is_game_started = False 
    
    game_result_text = ''
    game_result_color = None
    try_again_button_text = "다시 시도" # 기본 텍스트

    if status == 'win':
        game_result_text = 'I\'ve grown up perfectly!'
        game_result_color = WIN_COLOR
    else: # lose
        game_result_text = 'I\'ve grown up one more time!'
        game_result_color = LOSE_COLOR
        try_again_button_text = "Growing Up Again" # 패배 시 문구 변경
    
    # 화면을 반투명하게 덮습니다.
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((255, 255, 255, 150)) # 흰색에 투명도 150
    screen.blit(overlay, (0, 0))

    # 메시지 텍스트 렌더링 (폰트 크기 font_jua_medium으로 변경)
    # 테두리 효과를 위해 검은색 텍스트를 여러 번 오프셋하여 그립니다.
    border_offset = 2 # 테두리 두께 조절
    for dx in range(-border_offset, border_offset + 1):
        for dy in range(-border_offset, border_offset + 1):
            if dx != 0 or dy != 0: # 중앙은 제외
                border_text_surface = font_jua_medium.render(game_result_text, True, BLACK)
                border_text_rect = border_text_surface.get_rect(center=(SCREEN_WIDTH // 2 + dx, SCREEN_HEIGHT // 2 - 50 + dy))
                screen.blit(border_text_surface, border_text_rect)

    # 실제 텍스트를 그립니다.
    text_surface = font_jua_medium.render(game_result_text, True, game_result_color) 
    text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
    screen.blit(text_surface, text_rect)

    # '다시 시도' 버튼 렌더링 (폰트 크기 font_jua_small으로 변경)
    try_again_button_rect = pygame.Rect(0, 0, 200, 60)
    try_again_button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)
    draw_rounded_rect(screen, BUTTON_COLOR, try_again_button_rect, 10)
    try_again_text_surface = font_jua_small.render(try_again_button_text, True, WHITE) # 변경된 텍스트 사용
    try_again_text_rect = try_again_text_surface.get_rect(center=try_again_button_rect.center)
    screen.blit(try_again_text_surface, try_again_text_rect)
    pygame.display.flip() # 화면 업데이트

    # 버튼 클릭 또는 종료 대기
    waiting_for_input = True
    while waiting_for_input:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if try_again_button_rect.collidepoint(event.pos):
                    waiting_for_input = False
                    start_game() # 게임 재시작

def show_subliminal_message(row, col):
    """활성화된 메시지 목록에 서브리미널 메시지를 추가합니다."""
    message_text = random.choice(SUBLIMINAL_MESSAGES)
    x, y = get_tile_pixel_pos(row, col) # 타일의 실제 픽셀 위치
    
    # 메시지가 타일 중앙에서 살짝 위로 나타나도록 조정
    message_x = x + TILE_SIZE // 2
    message_y = y + TILE_SIZE // 2 - 20 
    active_subliminal_messages.append({
        'text': message_text,
        'x': message_x,
        'y': message_y,
        'start_time': time.time(),
        'initial_y': message_y # 위로 움직임을 위한 초기 Y 좌표 저장
    })

# --- 그리기 함수 ---

def draw_background_text():
    """배경에 'You're valuable.' 텍스트를 반복해서 그립니다."""
    text_content = "You're valuable."
    # 텍스트 표면을 한 번만 생성하고 회전
    text_surface_raw = font_jua_small.render(text_content, True, (255, 165, 0)) # 오렌지색
    rotated_text_surface = pygame.transform.rotate(text_surface_raw, 45) # 45도 회전
    
    # 투명도 조절을 위해 알파 채널이 있는 새 Surface 생성
    alpha_surface = pygame.Surface(rotated_text_surface.get_size(), pygame.SRCALPHA)
    alpha_surface.blit(rotated_text_surface, (0,0))
    alpha_surface.set_alpha(100) # 투명도 100 (0-255)

    rotated_text_rect = alpha_surface.get_rect()

    # 겹치지 않으면서 배경을 채우기 위한 간격 계산
    # 텍스트 길이에 따라 동적으로 간격을 조정합니다.
    # 대략적인 텍스트 너비와 높이를 고려하여 간격을 설정합니다.
    spacing_x = rotated_text_rect.width + 50 # 텍스트 너비 + 여백
    spacing_y = rotated_text_rect.height + 50 # 텍스트 높이 + 여백

    # 화면 전체를 회전된 텍스트로 채웁니다.
    # 화면 경계를 넘어가는 부분도 그리기 위해 시작점을 음수로 설정합니다.
    for x_offset in range(-rotated_text_rect.width, SCREEN_WIDTH + rotated_text_rect.width, spacing_x):
        for y_offset in range(-rotated_text_rect.height, SCREEN_HEIGHT + rotated_text_rect.height, spacing_y):
            screen.blit(alpha_surface, (x_offset, y_offset))


def draw_game_board_elements():
    """2048 게임 보드 요소 (격자 셀과 타일)를 그립니다."""
    current_time = time.time()

    board_offset_x = (SCREEN_WIDTH - BOARD_WIDTH) // 2
    board_offset_y = (SCREEN_HEIGHT - BOARD_HEIGHT) // 2 + 30 + 60

    # 격자 셀 그리기
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            x = board_offset_x + GAP + c * (TILE_SIZE + GAP)
            y = board_offset_y + GAP + r * (TILE_SIZE + GAP)
            # 투명한 색상으로 둥근 사각형을 직접 그립니다.
            draw_rounded_rect(screen, GRID_CELL_COLOR, pygame.Rect(x, y, TILE_SIZE, TILE_SIZE), 8)

    # Draw and animate tiles
    tiles_to_remove_from_active_list = []
    # 먼저 사라지는 타일을 그립니다 (다른 타일 위에 그려지지 않도록)
    for tile in all_active_tiles:
        if tile.is_disappearing:
            progress = (current_time - tile.animation_start_time) / MOVE_ANIMATION_DURATION
            progress = min(1.0, max(0.0, progress)) # 0과 1 사이로 클램프

            tile.alpha = int(255 * (1 - progress)) # 페이드 아웃
            
            # 사라지는 타일은 움직이지 않고 제자리에서 사라지게
            interp_x = tile.start_x
            interp_y = tile.start_y

            if progress >= 1.0:
                tiles_to_remove_from_active_list.append(tile) # 애니메이션 완료 시 제거

            if tile.alpha > 0: # 완전히 투명해지기 전까지만 그림
                tile_color = get_tile_color(tile.value)
                tile_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                draw_rounded_rect(tile_surface, tile_color, tile_surface.get_rect(), 8, border_width=1, border_color=(0,0,0,30))
                tile_surface.set_alpha(tile.alpha)
                
                tile_rect = tile_surface.get_rect(topleft=(interp_x, interp_y))
                screen.blit(tile_surface, tile_rect)

                # 숫자도 함께 페이드 아웃
                text_surface = font_jua_large.render(str(tile.value), True, TEXT_COLOR)
                text_surface.set_alpha(tile.alpha)
                text_rect = text_surface.get_rect(center=tile_rect.center)
                screen.blit(text_surface, text_rect)

    # 그 다음 움직이거나 새로 생성된 타일을 그립니다.
    for tile in all_active_tiles:
        if not tile.is_disappearing: # 사라지는 타일은 위에서 이미 그림
            progress = (current_time - tile.animation_start_time) / MOVE_ANIMATION_DURATION
            progress = min(1.0, max(0.0, progress)) # 0과 1 사이로 클램프

            # 이동 애니메이션
            interp_x = tile.start_x + (tile.end_x - tile.start_x) * progress
            interp_y = tile.start_y + (tile.end_y - tile.start_y) * progress

            # 새로 생성된 타일 페이드인
            if tile.is_new:
                tile.alpha = int(255 * progress)
                if progress >= 1.0:
                    tile.is_new = False # 애니메이션 완료
                    tile.alpha = 255 # 페이드인 완료 후 완전히 불투명하게 설정
            else:
                tile.alpha = 255 # 기본적으로 완전히 불투명하게 설정

            # 병합 결과 타일 애니메이션 (크기 펄스)
            scale_factor = 1.0
            if tile.is_merged_result:
                merge_progress = (current_time - tile.animation_start_time) / MERGE_ANIMATION_DURATION
                merge_progress = min(1.0, max(0.0, merge_progress))
                if merge_progress < 0.5:
                    scale_factor = 1.0 + 0.2 * merge_progress # 커짐
                else:
                    scale_factor = 1.1 - 0.2 * (merge_progress - 0.5) # 작아짐
                if merge_progress >= 1.0:
                    tile.is_merged_result = False # 애니메이션 완료

            tile_color = get_tile_color(tile.value)
            
            # 타일 표면 생성 및 알파 적용
            tile_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            draw_rounded_rect(tile_surface, tile_color, tile_surface.get_rect(), 8, border_width=1, border_color=(0,0,0,30))
            tile_surface.set_alpha(tile.alpha)

            # 병합 결과 타일 크기 조정
            if scale_factor != 1.0:
                scaled_width = int(TILE_SIZE * scale_factor)
                scaled_height = int(TILE_SIZE * scale_factor)
                tile_surface = pygame.transform.scale(tile_surface, (scaled_width, scaled_height))
            
            # 그리기 위치 조정 (중앙 정렬)
            tile_rect = tile_surface.get_rect(center=(interp_x + TILE_SIZE // 2, interp_y + TILE_SIZE // 2))
            screen.blit(tile_surface, tile_rect)

            # 타일 값 그리기
            text_surface = font_jua_large.render(str(tile.value), True, TEXT_COLOR)
            text_rect = text_surface.get_rect(center=(interp_x + TILE_SIZE // 2, interp_y + TILE_SIZE // 2))
            screen.blit(text_surface, text_rect)

    # 애니메이션이 끝난 사라지는 타일 제거
    for tile in tiles_to_remove_from_active_list:
        if tile in all_active_tiles: # 중복 제거 방지
            all_active_tiles.remove(tile)


    # 서브리미널 메시지 그리기
    messages_to_remove = []
    for msg in active_subliminal_messages:
        elapsed = current_time - msg['start_time']
        if elapsed < SUBLIMINAL_MESSAGE_DURATION:
            alpha = max(0, int(255 * (1 - (elapsed / SUBLIMINAL_MESSAGE_DURATION))))
            current_y = msg['initial_y'] - (elapsed / SUBLIMINAL_MESSAGE_DURATION) * 50
            
            text_surface = font_jua_subliminal.render(msg['text'], True, (76, 175, 80))
            text_surface.set_alpha(alpha)
            text_rect = text_surface.get_rect(center=(msg['x'], current_y))
            screen.blit(text_surface, text_rect)
        else:
            messages_to_remove.append(msg)
    
    for msg in messages_to_remove:
        active_subliminal_messages.remove(msg)


def draw_start_screen():
    """초기 시작 화면을 그립니다."""
    screen.fill(WHITE)
    draw_background_text() # 배경 텍스트 그리기

    title_surface = font_jua_title.render("2048", True, (76, 175, 80)) # #4CAF50
    title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
    screen.blit(title_surface, title_rect)

    start_button_rect = pygame.Rect(0, 0, 250, 80)
    start_button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)
    draw_rounded_rect(screen, START_BUTTON_COLOR, start_button_rect, 15)
    start_text = font_jua_medium.render("Let's growth!", True, WHITE) 
    start_text_rect = start_text.get_rect(center=start_button_rect.center)
    screen.blit(start_text, start_text_rect)

    pygame.display.flip() # 화면 업데이트
    return start_button_rect

def draw_game_screen():
    """메인 게임 화면을 그립니다."""
    screen.fill(WHITE) # 메인 배경
    draw_background_text() # 배경 텍스트
    
    # 게임 컨테이너 배경 그리기
    game_container_rect = pygame.Rect(
        (SCREEN_WIDTH - BOARD_WIDTH) // 2, 
        (SCREEN_HEIGHT - BOARD_HEIGHT) // 2 + 30, # 헤더 공간을 위해 조정
        BOARD_WIDTH, 
        BOARD_HEIGHT + 70 # 헤더 공간 추가
    )
    draw_rounded_rect(screen, LIGHT_ORANGE_BG, game_container_rect, 15)

    # 헤더 (버튼) 그리기
    reset_button_rect = pygame.Rect(0, 0, 150, 40)
    reset_button_rect.topright = (game_container_rect.right - 20, game_container_rect.top + 20)
    draw_rounded_rect(screen, BUTTON_COLOR, reset_button_rect, 10)
    reset_text = font_jua_small.render("Reset", True, WHITE) 
    reset_text_rect = reset_text.get_rect(center=reset_button_rect.center)
    screen.blit(reset_text, reset_text_rect)

    # 실제 게임 보드와 타일 그리기
    draw_game_board_elements() 
    
    return reset_button_rect

# --- 메인 게임 루프 ---
def game_loop():
    global is_game_started, is_game_over, is_game_won

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if not is_game_started:
                # 시작 화면 이벤트 처리
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if start_button_rect.collidepoint(event.pos):
                        initialize_game()
                        start_game()
            else:
                # 게임 이벤트 처리
                if event.type == pygame.KEYDOWN:
                    if not is_game_over and not is_game_won:
                        if event.key == pygame.K_LEFT:
                            move('left') 
                        elif event.key == pygame.K_RIGHT:
                            move('right')
                        elif event.key == pygame.K_UP:
                            move('up')
                        elif event.key == pygame.K_DOWN:
                            move('down') 
                        check_game_status() 

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # '다시 시작' 버튼 클릭 처리
                    if reset_button_rect.collidepoint(event.pos):
                        initialize_game()
                        start_game()
        
        # 화면 그리기
        screen.fill(WHITE) 
        draw_background_text() 

        if is_game_started:
            reset_button_rect = draw_game_screen() 
        else:
            start_button_rect = draw_start_screen() 

        pygame.display.flip() 
        clock.tick(60) 

    pygame.quit()
    sys.exit()

def start_game():
    """게임을 시작합니다 (시작 화면 숨기기, 초기 타일 추가)."""
    global is_game_started 
    is_game_started = True
    add_random_tile()
    add_random_tile()

# 초기 게임 설정 및 루프 시작
initialize_game()
game_loop()
