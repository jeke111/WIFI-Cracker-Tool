import pygame
import random
import sys

# 颜色定义
COLORS = {
    0: (204, 192, 179),
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

def init_grid():
    grid = [[0]*4 for _ in range(4)]
    add_new_number(grid)
    add_new_number(grid)
    return grid

def add_new_number(grid):
    empty_cells = [(i,j) for i in range(4) for j in range(4) if grid[i][j] == 0]
    if empty_cells:
        i, j = random.choice(empty_cells)
        grid[i][j] = 2 if random.random() < 0.9 else 4

# 在全局变量部分新增动画相关参数
ANIMATION_SPEED = 8  # 动画速度
animations = []      # 动画队列

def add_animation(start_pos, end_pos, value, is_merge=False):
    animations.append({
        'start': start_pos,
        'end': end_pos,
        'value': value,
        'progress': 0.0,
        'is_merge': is_merge
    })

# 修改网格绘制部分（添加圆角和渐变效果）
def draw_grid(screen, grid, score, font):
    global animations
    screen.fill((250, 248, 239))  # 更柔和的背景色
    
    # 绘制分数面板
    pygame.draw.rect(screen, (187, 173, 160), (15, 15, 200, 70), border_radius=8)
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (25, 30))
    
    # 绘制游戏主网格
    for i in range(4):
        for j in range(4):
            # 绘制网格单元格（带圆角）
            cell_rect = (j*100 + 20*(j+1), i*100 + 100 + 20*(i+1), 100, 100)
            pygame.draw.rect(screen, (119, 110, 101), cell_rect, border_radius=6)
            pygame.draw.rect(screen, (205, 193, 180), (cell_rect[0]+2, cell_rect[1]+2, 96, 96), border_radius=4)

    # 处理动画逻辑（优化位置计算）
    for anim in animations[:]:
        i1, j1 = anim['start']
        i2, j2 = anim['end']
        progress = min(anim['progress'] + 0.15, 1.0)  # 更平滑的动画速度
        
        # 计算动画位置（带缓动效果）
        x = j1 + (j2 - j1) * progress
        y = i1 + (i2 - i1) * progress
        size = 90 * (1 + 0.1 * (1 - abs(progress*2 -1))) if anim['is_merge'] else 90
        
        # 绘制动画方块（带阴影效果）
        pygame.draw.rect(screen, (0,0,0), 
                        (x*100 + 20*(x+1) + 5, y*100 + 100 + 20*(y+1) + 5 +3, 90, 90), 
                        border_radius=4, width=0)
        pygame.draw.rect(screen, COLORS.get(anim['value'], (0,0,0)),
                        (x*100 + 20*(x+1) + 5, y*100 + 100 + 20*(y+1) + 5, 90, 90), 
                        border_radius=4)
        
        # 更新动画进度
        if progress >= 1.0:
            animations.remove(anim)
        else:
            anim['progress'] = progress

    # 绘制静态方块（最后渲染确保在动画上方）
    for i in range(4):
        for j in range(4):
            if grid[i][j] != 0 and not any(a['end'] == (i,j) for a in animations):
                # 绘制带阴影的方块
                pygame.draw.rect(screen, (0,0,0), 
                                (j*100 + 20*(j+1) + 5, i*100 + 100 + 20*(i+1) + 5 +3, 90, 90), 
                                border_radius=4, width=0)
                pygame.draw.rect(screen, COLORS.get(grid[i][j], (0,0,0)),
                                (j*100 + 20*(j+1) + 5, i*100 + 100 + 20*(i+1) + 5, 90, 90), 
                                border_radius=4)
                # 绘制数字（自动缩放）
                text_size = 50 if grid[i][j] < 100 else 40
                text = pygame.font.Font(None, text_size).render(str(grid[i][j]), True, (255, 255, 255))
                text_rect = text.get_rect(center=(j*100 + 20*(j+1)+50, i*100 + 100 + 20*(i+1)+50))
                screen.blit(text, text_rect)

# 在move函数中记录动画路径
def move(grid, direction):
    global animations
    moved = False
    score = 0
    animations.clear()
    
    # 矩阵转置处理垂直移动
    if direction in ('up', 'down'):
        grid = list(map(list, zip(*grid)))
    
    for i in range(4):
        # 过滤非零元素
        nums = [num for num in grid[i] if num]
        
        # 处理合并
        if direction in ('left', 'up'):
            for j in range(len(nums)-1):
                if nums[j] == nums[j+1]:
                    nums[j] *= 2
                    score += nums[j]
                    nums[j+1] = 0
            nums = [num for num in nums if num]
            nums += [0]*(4-len(nums))
        else:  # right/down方向
            for j in range(len(nums)-1,0,-1):
                if nums[j] == nums[j-1]:
                    nums[j] *= 2
                    score += nums[j]
                    nums[j-1] = 0
            nums = [num for num in nums if num]
            nums = [0]*(4-len(nums)) + nums
        
        if nums != grid[i]:
            moved = True
        grid[i] = nums
    
    # 转置回原方向
    if direction in ('up', 'down'):
        grid = list(map(list, zip(*grid)))
    
    return grid, moved, score

def is_game_over(grid):
    for i in range(4):
        for j in range(4):
            if grid[i][j] == 0:
                return False
            if i < 3 and grid[i][j] == grid[i+1][j]:
                return False
            if j < 3 and grid[i][j] == grid[i][j+1]:
                return False
    return True

def main():
    pygame.init()
    screen = pygame.display.set_mode((480, 680))
    pygame.display.set_caption("2048")
    font = pygame.font.Font(None, 36)
    big_font = pygame.font.Font(None, 50)
    
    grid = init_grid()
    score = 0
    
    clock = pygame.time.Clock()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                    
                dir_map = {
                    pygame.K_UP: 'up',
                    pygame.K_DOWN: 'down',
                    pygame.K_LEFT: 'left',
                    pygame.K_RIGHT: 'right'
                }
                
                if event.key in dir_map:
                    direction = dir_map[event.key]
                    new_grid, moved, delta_score = move([row[:] for row in grid], direction)
                    if moved:
                        grid = new_grid
                        score += delta_score
                        add_new_number(grid)
        
        draw_grid(screen, grid, score, big_font)
        
        if is_game_over(grid):
            game_over_text = big_font.render("Game Over!", True, (119, 110, 101))
            screen.blit(game_over_text, (120, 300))
        
        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    main()