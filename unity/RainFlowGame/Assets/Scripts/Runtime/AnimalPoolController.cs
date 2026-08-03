using System.Collections.Generic;
using UnityEngine;

namespace RainFlow.Game
{
    public sealed class AnimalPoolController : MonoBehaviour
    {
        private const int MaxCats = 120;
        private const int MaxDogs = 40;

        private sealed class PooledAnimal
        {
            public GameObject Root;
            public int RouteIndex;
            public float Progress;
            public float Speed;
            public Vector3 Anchor;
            public float Phase;
        }

        private readonly List<PooledAnimal> _cats = new List<PooledAnimal>();
        private readonly List<PooledAnimal> _dogs = new List<PooledAnimal>();
        private readonly List<List<Vector3>> _routes = new List<List<Vector3>>();
        private Camera _camera;
        private float _trafficIntensity = 0.35f;
        private int _buildingLevel = 1;
        private bool _alternateSkin;

        private void Awake()
        {
            _camera = Camera.main;
            var sprite = MapWorldController.CreateSquareSprite();
            for (var index = 0; index < MaxCats; index++)
            {
                _cats.Add(CreateCat(index, sprite));
            }
            for (var index = 0; index < MaxDogs; index++)
            {
                _dogs.Add(CreateDog(index, sprite));
            }
            SetAlternateSkin(false);
            RefreshActiveCounts();
        }

        public void ConfigureRoutes(IReadOnlyList<List<Vector3>> routes)
        {
            _routes.Clear();
            foreach (var route in routes)
            {
                if (route != null && route.Count >= 2) _routes.Add(route);
            }
            for (var index = 0; index < _cats.Count; index++)
            {
                _cats[index].RouteIndex = _routes.Count == 0 ? 0 : index % _routes.Count;
            }
        }

        public void ApplyState(float occupancy, int buildingLevel)
        {
            _trafficIntensity = Mathf.Clamp01(occupancy);
            _buildingLevel = Mathf.Clamp(buildingLevel, 1, 3);
            RefreshActiveCounts();
        }

        public void SetAlternateSkin(bool enabled)
        {
            _alternateSkin = enabled;
            var catColor = enabled ? new Color(0.66f, 0.45f, 0.95f) : new Color(1f, 0.63f, 0.24f);
            var dogColor = enabled ? new Color(0.27f, 0.82f, 0.95f) : new Color(0.92f, 0.86f, 0.69f);
            Recolor(_cats, catColor);
            Recolor(_dogs, dogColor);
        }

        private void Update()
        {
            var detailVisible = _camera == null || _camera.orthographicSize < 700f;
            for (var index = 0; index < _cats.Count; index++)
            {
                var cat = _cats[index];
                if (!cat.Root.activeSelf || !detailVisible)
                {
                    cat.Root.SetActive(false);
                    continue;
                }
                MoveCat(cat);
            }
            for (var index = 0; index < _dogs.Count; index++)
            {
                var dog = _dogs[index];
                if (!dog.Root.activeSelf || !detailVisible)
                {
                    dog.Root.SetActive(false);
                    continue;
                }
                dog.Phase += Time.deltaTime * dog.Speed;
                dog.Root.transform.position = dog.Anchor + new Vector3(
                    Mathf.Sin(dog.Phase) * 18f,
                    Mathf.Cos(dog.Phase * 0.73f) * 12f,
                    0f);
            }

            if (detailVisible) RefreshActiveCounts();
        }

        private void MoveCat(PooledAnimal animal)
        {
            if (_routes.Count == 0) return;
            var route = _routes[animal.RouteIndex % _routes.Count];
            animal.Progress = Mathf.Repeat(
                animal.Progress + Time.deltaTime * animal.Speed / Mathf.Max(1, route.Count - 1),
                1f);
            var scaled = animal.Progress * (route.Count - 1);
            var from = Mathf.Clamp(Mathf.FloorToInt(scaled), 0, route.Count - 2);
            var amount = scaled - from;
            var start = route[from];
            var end = route[from + 1];
            animal.Root.transform.position = Vector3.Lerp(start, end, amount) + new Vector3(0, 0, -12f);
            var direction = end - start;
            animal.Root.transform.rotation = Quaternion.Euler(
                0,
                0,
                Mathf.Atan2(direction.y, direction.x) * Mathf.Rad2Deg);
        }

        private void RefreshActiveCounts()
        {
            var catCount = Mathf.RoundToInt(Mathf.Lerp(18, MaxCats, _trafficIntensity));
            var dogCount = Mathf.Clamp(10 + _buildingLevel * 10, 0, MaxDogs);
            SetPoolActive(_cats, catCount);
            SetPoolActive(_dogs, dogCount);
        }

        private static void SetPoolActive(List<PooledAnimal> pool, int count)
        {
            for (var index = 0; index < pool.Count; index++)
            {
                pool[index].Root.SetActive(index < count);
            }
        }

        private static void Recolor(List<PooledAnimal> pool, Color color)
        {
            foreach (var animal in pool)
            {
                var renderers = animal.Root.GetComponentsInChildren<SpriteRenderer>(true);
                foreach (var renderer in renderers) renderer.color = color;
            }
        }

        private PooledAnimal CreateCat(int index, Sprite sprite)
        {
            var root = new GameObject("Cat Car " + index);
            root.transform.SetParent(transform);
            AddPart(root.transform, sprite, Vector3.zero, new Vector3(18f, 10f, 1f), 30);
            AddPart(root.transform, sprite, new Vector3(-5f, 7f), new Vector3(5f, 5f, 1f), 31);
            AddPart(root.transform, sprite, new Vector3(5f, 7f), new Vector3(5f, 5f, 1f), 31);
            AddPart(root.transform, sprite, new Vector3(-12f, 1f), new Vector3(8f, 3f, 1f), 29);
            return new PooledAnimal
            {
                Root = root,
                RouteIndex = index,
                Progress = Mathf.Repeat(index * 0.077f, 1f),
                Speed = 0.5f + (index % 7) * 0.08f
            };
        }

        private PooledAnimal CreateDog(int index, Sprite sprite)
        {
            var root = new GameObject("Dog Pedestrian " + index);
            root.transform.SetParent(transform);
            AddPart(root.transform, sprite, Vector3.zero, new Vector3(8f, 12f, 1f), 32);
            AddPart(root.transform, sprite, new Vector3(0f, 9f), new Vector3(7f, 7f, 1f), 33);
            AddPart(root.transform, sprite, new Vector3(5f, 12f), new Vector3(3f, 6f, 1f), 32);
            var column = index % 8;
            var row = index / 8;
            return new PooledAnimal
            {
                Root = root,
                Anchor = new Vector3(-350f + column * 100f, -180f + row * 90f, -14f),
                Phase = index * 0.7f,
                Speed = 0.55f + (index % 5) * 0.07f
            };
        }

        private static void AddPart(
            Transform parent,
            Sprite sprite,
            Vector3 localPosition,
            Vector3 scale,
            int sortingOrder)
        {
            var part = new GameObject("Part");
            part.transform.SetParent(parent);
            part.transform.localPosition = localPosition;
            part.transform.localScale = scale;
            var renderer = part.AddComponent<SpriteRenderer>();
            renderer.sprite = sprite;
            renderer.sortingOrder = sortingOrder;
            renderer.color = new Color(1f, 0.63f, 0.24f);
        }
    }
}
