#include "../include/fleet.hpp"

Fleet::Fleet(int _id, int _cell_size, float _velocity)
    : id(_id), cell_size(_cell_size), velocity(_velocity), G()
{
}

Agent::Agent(int _id, int _fleet_id)
    : id(_id), fleet_id(_fleet_id), priority(0.0f)
{
}

CollisionChecker::CollisionChecker() : base_width(0), base_height(0) {}

CollisionChecker::CollisionChecker(const Fleets& fleets, int _base_width,
                                   int _base_height)
    : base_width(_base_width), base_height(_base_height)
{
  grid_sizes.resize(fleets.size());
  for (auto* f : fleets) {
    grid_sizes[f->id] = static_cast<float>(f->cell_size);
  }
}

std::vector<int> CollisionChecker::to_base_cells(int fleet_id, int cell_index,
                                                 int fleet_width) const
{
  int cs = static_cast<int>(grid_sizes[fleet_id]);
  int fx = cell_index % fleet_width;
  int fy = cell_index / fleet_width;

  std::vector<int> base_cells;
  base_cells.reserve(cs * cs);
  for (int dy = 0; dy < cs; ++dy) {
    for (int dx = 0; dx < cs; ++dx) {
      int bx = fx * cs + dx;
      int by = fy * cs + dy;
      if (bx < base_width && by < base_height) {
        base_cells.push_back(base_width * by + bx);
      }
    }
  }
  return base_cells;
}

std::pair<int, int> CollisionChecker::to_grid_space(int fleet_id, float wx,
                                                    float wy) const
{
  float cs = grid_sizes[fleet_id];
  return {static_cast<int>(std::floor(wx / cs)),
          static_cast<int>(std::floor(wy / cs))};
}

std::vector<std::pair<int, int>> CollisionChecker::get_blocked_nodes(
    int fleet_id, int x, int y, const Fleets& fleets) const
{
  float cs = grid_sizes[fleet_id];
  // real-world bounding box of this cell
  float rw_x0 = x * cs;
  float rw_y0 = y * cs;
  float rw_x1 = rw_x0 + cs;
  float rw_y1 = rw_y0 + cs;

  std::vector<std::pair<int, int>> result;

  for (size_t fid = 0; fid < fleets.size(); ++fid) {
    if (static_cast<int>(fid) == fleet_id) continue;

    float other_cs = grid_sizes[fid];
    int other_w = fleets[fid]->G.width;
    int other_h = fleets[fid]->G.height;
    if (other_w == 0 || other_h == 0) continue;

    // find overlapping cell range on the other fleet's graph
    int sx = static_cast<int>(std::floor(rw_x0 / other_cs));
    int sy = static_cast<int>(std::floor(rw_y0 / other_cs));
    int ex = static_cast<int>(std::ceil(rw_x1 / other_cs));
    int ey = static_cast<int>(std::ceil(rw_y1 / other_cs));

    // clamp to grid bounds
    sx = std::max(0, sx);
    sy = std::max(0, sy);
    ex = std::min(ex, other_w);
    ey = std::min(ey, other_h);

    for (int oy = sy; oy < ey; ++oy) {
      for (int ox = sx; ox < ex; ++ox) {
        result.push_back({static_cast<int>(fid), other_w * oy + ox});
      }
    }
  }
  return result;
}
