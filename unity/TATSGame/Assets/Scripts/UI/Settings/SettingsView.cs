using System;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Game.UI.Settings
{
    /// <summary>
    /// SettingsScreen.uxml을 그리는 UIDocument에 붙는 얇은 부트스트랩. 서버 연결 없이 뜬다
    /// (docs/23_TITLE_SCREEN_BACKLOG.md T4). 저장 파일 위치는 <c>Application.persistentDataPath</c>
    /// 바로 아래 <c>settings.json</c>으로 고정했다 — 문서 어디에도 경로 규정이 없는 Unity 쪽
    /// 구현 결정이다(T3의 GameSave 슬롯 디렉터리와 같은 근거).
    ///
    /// 실제 씬에 이 컴포넌트를 붙이고 시작 화면과의 전환을 연결하는 작업은 Unity Editor가 필요해
    /// 사람이 로컬에서 한다 — T1~T3와 같은 이유.
    /// </summary>
    [RequireComponent(typeof(UIDocument))]
    public sealed class SettingsView : MonoBehaviour
    {
        SettingsPresenter _presenter;

        public event Action Back;
        public event Action<GameSettings> Saved;

        public SettingsPresenter Presenter => _presenter;

        void OnEnable()
        {
            var document = GetComponent<UIDocument>();
            var store = new GameSettingsStore(Application.persistentDataPath);
            _presenter = new SettingsPresenter(document.rootVisualElement, store);
            _presenter.Back += OnBack;
            _presenter.Saved += OnSaved;
        }

        void OnDisable()
        {
            if (_presenter == null)
            {
                return;
            }

            _presenter.Back -= OnBack;
            _presenter.Saved -= OnSaved;
            _presenter.Dispose();
            _presenter = null;
        }

        void OnBack()
        {
            Back?.Invoke();
        }

        void OnSaved(GameSettings settings)
        {
            Saved?.Invoke(settings);
        }
    }
}
