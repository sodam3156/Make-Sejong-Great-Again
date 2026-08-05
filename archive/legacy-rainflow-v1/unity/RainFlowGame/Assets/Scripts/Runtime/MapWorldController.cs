using System;
using System.Collections.Generic;
using System.IO;
using Newtonsoft.Json;
using UnityEngine;

namespace RainFlow.Game
{
    public sealed class MapWorldController : MonoBehaviour
    {
        private readonly Dictionary<string, GameObject> _regionNodes = new Dictionary<string, GameObject>();
        private readonly Dictionary<string, GameObject> _buildings = new Dictionary<string, GameObject>();
        private readonly List<List<Vector3>> _routes = new List<List<Vector3>>();
        private GameObject _majorRoads;
        private GameObject _minorRoads;
        private Camera _camera;
        private string _selectedRegion;
        private Material _majorMaterial;
        private Material _minorMaterial;

        public event Action<IReadOnlyList<List<Vector3>>> MapLoaded;
        public IReadOnlyList<List<Vector3>> Routes { get { return _routes; } }

        private void Awake()
        {
            _camera = Camera.main;
            if (_camera == null)
            {
                var cameraObject = new GameObject("RainFlow Camera");
                cameraObject.tag = "MainCamera";
                _camera = cameraObject.AddComponent<Camera>();
                _camera.orthographic = true;
                _camera.orthographicSize = 1300f;
                _camera.transform.position = new Vector3(0, 0, -100f);
                _camera.backgroundColor = new Color(0.055f, 0.075f, 0.10f);
                _camera.clearFlags = CameraClearFlags.SolidColor;
                cameraObject.AddComponent<MapCameraController>();
            }
            LoadMap();
        }

        private void Update()
        {
            if (_camera == null) return;
            var size = _camera.orthographicSize;
            if (_minorRoads != null) _minorRoads.SetActive(size < 1150f);
            foreach (var building in _buildings.Values)
            {
                building.SetActive(size < 1600f);
            }
        }

        public void SetSelectedRegion(string regionId)
        {
            _selectedRegion = regionId;
            foreach (var pair in _regionNodes)
            {
                var renderer = pair.Value.GetComponent<SpriteRenderer>();
                renderer.color = pair.Key == _selectedRegion
                    ? new Color(1f, 0.76f, 0.25f)
                    : new Color(0.25f, 0.82f, 0.72f);
            }
        }

        public void SetBuildingLevel(string regionId, int level)
        {
            GameObject building;
            if (!_buildings.TryGetValue(regionId, out building)) return;
            var safeLevel = Mathf.Clamp(level, 1, 3);
            building.transform.localScale = new Vector3(
                42f + safeLevel * 18f,
                52f + safeLevel * 28f,
                1f);
            building.GetComponent<SpriteRenderer>().color = safeLevel >= 3
                ? new Color(1f, 0.58f, 0.28f)
                : safeLevel == 2
                    ? new Color(0.52f, 0.67f, 1f)
                    : new Color(0.38f, 0.47f, 0.62f);
        }

        public void ApplyCongestion(float occupancy)
        {
            if (_majorMaterial == null) return;
            _majorMaterial.color = Color.Lerp(
                new Color(0.24f, 0.72f, 0.64f),
                new Color(0.96f, 0.30f, 0.28f),
                Mathf.Clamp01(occupancy));
        }

        private void LoadMap()
        {
            try
            {
                var path = Path.Combine(Application.streamingAssetsPath, "map", "eojin_map.json");
                var map = JsonConvert.DeserializeObject<GameMapDto>(File.ReadAllText(path));
                BuildRoadMeshes(map);
                BuildRegions(map);
                if (MapLoaded != null) MapLoaded(_routes);
            }
            catch (Exception error)
            {
                Debug.LogError("RainFlow map load failed: " + error.Message);
            }
        }

        private void BuildRoadMeshes(GameMapDto map)
        {
            var major = new List<RoadDto>();
            var minor = new List<RoadDto>();
            foreach (var road in map.Roads)
            {
                if (road.Lanes >= 2) major.Add(road); else minor.Add(road);
                if (road.Lanes >= 3 || road.Points.Count >= 8)
                {
                    var route = new List<Vector3>();
                    foreach (var point in road.Points)
                    {
                        if (point.Length >= 2) route.Add(new Vector3(point[0], point[1], -2f));
                    }
                    if (route.Count >= 2) _routes.Add(route);
                }
            }
            _majorMaterial = NewMaterial(new Color(0.24f, 0.72f, 0.64f));
            _minorMaterial = NewMaterial(new Color(0.18f, 0.23f, 0.31f));
            _majorRoads = CreateRoadObject("Major Roads", major, _majorMaterial, -1f);
            _minorRoads = CreateRoadObject("Minor Roads", minor, _minorMaterial, 0f);
        }

        private static GameObject CreateRoadObject(
            string name,
            List<RoadDto> roads,
            Material material,
            float z)
        {
            var vertices = new List<Vector3>();
            var triangles = new List<int>();
            foreach (var road in roads)
            {
                var width = Mathf.Clamp(road.Lanes * 3.5f, 3.5f, 14f);
                for (var index = 0; index + 1 < road.Points.Count; index++)
                {
                    var left = road.Points[index];
                    var right = road.Points[index + 1];
                    if (left.Length < 2 || right.Length < 2) continue;
                    var start = new Vector2(left[0], left[1]);
                    var end = new Vector2(right[0], right[1]);
                    var delta = end - start;
                    if (delta.sqrMagnitude < 0.01f) continue;
                    var normal = new Vector2(-delta.y, delta.x).normalized * width * 0.5f;
                    var first = vertices.Count;
                    vertices.Add(new Vector3(start.x - normal.x, start.y - normal.y, z));
                    vertices.Add(new Vector3(start.x + normal.x, start.y + normal.y, z));
                    vertices.Add(new Vector3(end.x + normal.x, end.y + normal.y, z));
                    vertices.Add(new Vector3(end.x - normal.x, end.y - normal.y, z));
                    triangles.Add(first);
                    triangles.Add(first + 1);
                    triangles.Add(first + 2);
                    triangles.Add(first);
                    triangles.Add(first + 2);
                    triangles.Add(first + 3);
                }
            }
            var mesh = new Mesh { name = name + " Mesh" };
            mesh.SetVertices(vertices);
            mesh.SetTriangles(triangles, 0);
            mesh.RecalculateBounds();
            var gameObject = new GameObject(name);
            gameObject.AddComponent<MeshFilter>().sharedMesh = mesh;
            gameObject.AddComponent<MeshRenderer>().sharedMaterial = material;
            return gameObject;
        }

        private void BuildRegions(GameMapDto map)
        {
            var sprite = CreateSquareSprite();
            foreach (var region in map.Regions)
            {
                if (region.Position == null || region.Position.Length < 2) continue;
                var position = new Vector3(region.Position[0], region.Position[1], -8f);

                var node = new GameObject("Region " + region.RegionId);
                node.transform.position = position;
                node.transform.localScale = new Vector3(70f, 70f, 1f);
                var nodeRenderer = node.AddComponent<SpriteRenderer>();
                nodeRenderer.sprite = sprite;
                nodeRenderer.color = new Color(0.25f, 0.82f, 0.72f);
                nodeRenderer.sortingOrder = 20;
                _regionNodes[region.RegionId] = node;

                var building = new GameObject("Building " + region.RegionId);
                building.transform.position = position + new Vector3(90f, 65f, 1f);
                var buildingRenderer = building.AddComponent<SpriteRenderer>();
                buildingRenderer.sprite = sprite;
                buildingRenderer.sortingOrder = 15;
                _buildings[region.RegionId] = building;
                SetBuildingLevel(region.RegionId, 1);
            }
        }

        private static Material NewMaterial(Color color)
        {
            var shader = Shader.Find("Sprites/Default");
            var material = new Material(shader) { color = color };
            return material;
        }

        public static Sprite CreateSquareSprite()
        {
            var texture = new Texture2D(1, 1, TextureFormat.RGBA32, false);
            texture.SetPixel(0, 0, Color.white);
            texture.Apply();
            texture.filterMode = FilterMode.Point;
            return Sprite.Create(texture, new Rect(0, 0, 1, 1), new Vector2(0.5f, 0.5f), 1f);
        }
    }

    public sealed class MapCameraController : MonoBehaviour
    {
        private Camera _camera;
        private Vector3 _dragOrigin;

        private void Awake()
        {
            _camera = GetComponent<Camera>();
        }

        private void Update()
        {
            var scroll = Input.mouseScrollDelta.y;
            if (Mathf.Abs(scroll) > 0.01f)
            {
                _camera.orthographicSize = Mathf.Clamp(
                    _camera.orthographicSize * (1f - scroll * 0.12f),
                    250f,
                    1800f);
            }
            if (Input.GetMouseButtonDown(2))
            {
                _dragOrigin = _camera.ScreenToWorldPoint(Input.mousePosition);
            }
            if (Input.GetMouseButton(2))
            {
                var current = _camera.ScreenToWorldPoint(Input.mousePosition);
                var difference = _dragOrigin - current;
                transform.position += new Vector3(difference.x, difference.y, 0f);
                transform.position = new Vector3(
                    Mathf.Clamp(transform.position.x, -2200f, 2200f),
                    Mathf.Clamp(transform.position.y, -900f, 900f),
                    -100f);
            }
        }
    }
}
