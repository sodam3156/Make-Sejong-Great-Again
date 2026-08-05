using System;
using UnityEngine;
using UnityEngine.UIElements;

namespace Tats.Game.UI.TitleScreen
{
    /// <summary>
    /// TitleScreen.uxml을 그리는 UIDocument에 붙는 얇은 부트스트랩. 서버 연결 없이 뜬다
    /// (docs/23_TITLE_SCREEN_BACKLOG.md T1). 실제 씬에 이 컴포넌트를 붙이는 작업은
    /// Unity Editor가 필요해 사람이 로컬에서 한다.
    /// </summary>
    [RequireComponent(typeof(UIDocument))]
    public sealed class TitleScreenView : MonoBehaviour
    {
        TitleScreenPresenter _presenter;

        public event Action<TitleScreenMenuItem> MenuItemActivated;

        void OnEnable()
        {
            var document = GetComponent<UIDocument>();
            _presenter = new TitleScreenPresenter(document.rootVisualElement);
            _presenter.MenuItemActivated += OnMenuItemActivated;
        }

        void OnDisable()
        {
            if (_presenter == null)
            {
                return;
            }

            _presenter.MenuItemActivated -= OnMenuItemActivated;
            _presenter.Dispose();
            _presenter = null;
        }

        void OnMenuItemActivated(TitleScreenMenuItem item)
        {
            MenuItemActivated?.Invoke(item);
        }
    }
}
